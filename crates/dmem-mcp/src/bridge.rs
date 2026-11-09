//! One public stdio browser connection, native ownership checks, then signed private intake.
use dmem_client::DmemClient;
use dmem_contracts::{CopyMode, FormInput, WebClipInput, WebKind};
use serde::Deserialize;
use serde_json::{Value, json};
use std::{
    collections::HashSet,
    path::PathBuf,
    time::{Duration, SystemTime, UNIX_EPOCH},
};
use tokio::{
    io::{AsyncBufReadExt, AsyncWriteExt, BufReader},
    process::{Child, ChildStdin, ChildStdout, Command},
};

const CLIENT: &str = "dmem-browser-mcp";
const CLIP: &str = "document_memory_clip_current_tab";
const CLIP_ALIAS: &str = "doc_memory_clip_current_tab";
fn now_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}
/// Public session names are insufficient. Native evaluation on this retained connection
/// must also succeed, and the exact target is checked again before any persistence.
pub fn validate_target(context: &Value, session: &str) -> Result<Value, String> {
    let invalid = || "browser_target_unavailable".to_string();
    if context["ok"] != true
        || context["session_id"] != session
        || context["has_local_lease"] == false
    {
        return Err(invalid());
    }
    let tab = context["tabs"]
        .as_array()
        .and_then(|tabs| {
            tabs.iter().find(|t| {
                t["tab_id"] == context["automation_target_tab"] && t["is_automation_target"] == true
            })
        })
        .ok_or_else(invalid)?;
    let owner = &tab["owner"];
    if tab["is_mine"] != true
        || tab["ready"] != true
        || tab["has_local_lease"] == false
        || owner["has_local_lease"] == false
        || owner["is_mine"] != true
        || owner["session_id"] != session
        || owner["client_name"] != CLIENT
        || owner["window_id"] != tab["window_id"]
        || owner["tab_id"] != tab["tab_id"]
        || owner["expires_at_ms"]
            .as_u64()
            .is_none_or(|n| n <= now_ms())
        || !tab["url"].is_string()
        || !tab["tab_id"].is_u64()
        || !tab["window_id"].is_u64()
    {
        return Err(invalid());
    }
    Ok(tab.clone())
}
fn tool_value(result: Value) -> Result<Value, String> {
    if result["isError"] == true {
        return Err("browser_unavailable".into());
    }
    let value = if let Some(value) = result.get("structuredContent") {
        value.clone()
    } else {
        serde_json::from_str(
            result["content"][0]["text"]
                .as_str()
                .ok_or("browser_unavailable")?,
        )
        .map_err(|_| "browser_unavailable")?
    };
    Ok(value.get("reply").cloned().unwrap_or(value))
}
struct Wire {
    child: Child,
    input: ChildStdin,
    output: BufReader<ChildStdout>,
    id: u64,
    names: HashSet<String>,
}
impl Wire {
    fn spawn(path: PathBuf, args: Vec<String>) -> Result<Self, String> {
        if !path.is_absolute() || !path.is_file() {
            return Err("invalid_input".into());
        }
        let mut child = Command::new(path)
            .args(args)
            .env_remove("DMEM_TOKEN")
            .env_remove("DMEM_CAPTURE_SECRET")
            .env_remove("DMEM_ADMIN_TOKEN")
            .stdin(std::process::Stdio::piped())
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::null())
            .kill_on_drop(true)
            .spawn()
            .map_err(|_| "browser_unavailable")?;
        let input = child.stdin.take().ok_or("browser_unavailable")?;
        let output = BufReader::new(child.stdout.take().ok_or("browser_unavailable")?);
        Ok(Self {
            child,
            input,
            output,
            id: 1000,
            names: HashSet::new(),
        })
    }
    async fn send(&mut self, value: &Value) -> Result<(), String> {
        let mut bytes = serde_json::to_vec(value).map_err(|_| "invalid_input")?;
        bytes.push(b'\n');
        self.input
            .write_all(&bytes)
            .await
            .map_err(|_| "browser_unavailable")?;
        self.input
            .flush()
            .await
            .map_err(|_| "browser_unavailable".into())
    }
    async fn rpc(&mut self, method: &str, params: Value) -> Result<Value, String> {
        self.id += 1;
        let id = self.id;
        self.send(&json!({"jsonrpc":"2.0","id":id,"method":method,"params":params}))
            .await?;
        tokio::time::timeout(Duration::from_secs(60), async {
            for _ in 0..128 {
                let mut bytes = Vec::new();
                // Do not allow an unbounded line from a misconfigured child.
                loop {
                    let available = self
                        .output
                        .fill_buf()
                        .await
                        .map_err(|_| "browser_unavailable")?;
                    if available.is_empty() {
                        return Err("browser_unavailable".into());
                    }
                    let n = available
                        .iter()
                        .position(|b| *b == b'\n')
                        .map_or(available.len(), |n| n + 1);
                    if bytes.len() + n > 32 * 1024 * 1024 {
                        return Err("browser_response_too_large".into());
                    }
                    let done = available[..n].last() == Some(&b'\n');
                    bytes.extend_from_slice(&available[..n]);
                    self.output.consume(n);
                    if done {
                        break;
                    }
                }
                let value: Value =
                    serde_json::from_slice(&bytes).map_err(|_| "browser_unavailable")?;
                if value["id"] == id {
                    if value.get("error").is_some() {
                        return Err("browser_unavailable".into());
                    }
                    return value
                        .get("result")
                        .cloned()
                        .ok_or_else(|| "browser_unavailable".into());
                }
            }
            Err("browser_unavailable".into())
        })
        .await
        .map_err(|_| "browser_timeout".to_string())?
    }
    async fn call(&mut self, name: &str, args: Value) -> Result<Value, String> {
        self.rpc("tools/call", json!({"name":name,"arguments":args}))
            .await
    }
    async fn catalog(&mut self) -> Result<Value, String> {
        let browser = self.rpc("tools/list", json!({})).await?;
        let mut tools = browser["tools"]
            .as_array()
            .cloned()
            .ok_or("browser_unavailable")?;
        if browser.get("nextCursor").is_some_and(|v| !v.is_null()) {
            return Err("browser_catalog_incomplete".into());
        }
        self.names = tools
            .iter()
            .filter_map(|t| t["name"].as_str().map(String::from))
            .collect();
        if !["browser_tabs", "browser_eval"]
            .iter()
            .all(|name| self.names.contains(*name))
        {
            return Err("browser_unsupported".into());
        }
        tools.extend(crate::tools().as_array().cloned().unwrap_or_default());
        for name in [CLIP, CLIP_ALIAS] {
            tools.push(json!({"name":name,"description":"Capture visible document structure or permitted reference text from this session's owned browser tab. Verify tab ownership and URL before and after capture. Requires explicit user intent; never accepts a URL or HTML from the model. Saves privately, never publishes.","annotations":{"readOnlyHint":false,"destructiveHint":false,"openWorldHint":false},"inputSchema":{"type":"object","properties":{"session_id":{"type":"string","minLength":1,"maxLength":200},"kind":{"enum":["template","reference"]},"title":{"type":"string","maxLength":120},"form":{"type":"object"},"copy_mode":{"enum":["structure_only","full"]}},"required":["session_id"],"additionalProperties":false}}));
        }
        let mut names = HashSet::new();
        if tools
            .iter()
            .any(|t| !names.insert(t["name"].as_str().unwrap_or("").to_owned()))
        {
            return Err("browser_tool_collision".into());
        }
        Ok(json!({"tools":tools}))
    }
    async fn clip(
        &mut self,
        client: &DmemClient,
        args: Value,
        secret: Option<&str>,
    ) -> Result<Value, String> {
        let input: ClipArgs = serde_json::from_value(args).map_err(|_| "invalid_input")?;
        if input.session_id.is_empty()
            || input.session_id.len() > 200
            || !input
                .session_id
                .bytes()
                .all(|b| b.is_ascii_alphanumeric() || b"_-".contains(&b))
        {
            return Err("invalid_input".into());
        }
        let secret = secret
            .filter(|s| s.len() >= 32)
            .ok_or("capture_not_configured")?;
        let before = tool_value(
            self.call("browser_tabs", json!({"session_id":input.session_id}))
                .await?,
        )?;
        let target = validate_target(&before, &input.session_id)?;
        // Native browser_eval itself requires this connection's private lease proof.
        // Legacy Arise versions omit has_local_lease from browser_tabs, so names alone
        // never authorize capture: evaluation must succeed and the target must remain.
        let evaluated = tool_value(
            self.call(
                "browser_eval",
                json!({"session_id":input.session_id,"js":CAPTURE_JS}),
            )
            .await?,
        )?;
        let captured: Value =
            serde_json::from_str(evaluated["result"].as_str().ok_or("browser_unavailable")?)
                .map_err(|_| "browser_unavailable")?;
        if captured["blocked"] == true {
            return Err("fetch_blocked".into());
        }
        let after = tool_value(
            self.call("browser_tabs", json!({"session_id":input.session_id}))
                .await?,
        )?;
        let after = validate_target(&after, &input.session_id)?;
        if ["tab_id", "window_id", "url"]
            .iter()
            .any(|k| target[*k] != after[*k])
            || captured["url"] != target["url"]
        {
            return Err("browser_target_changed".into());
        }
        let html = captured["html"]
            .as_str()
            .filter(|s| s.len() <= 1024 * 1024)
            .ok_or("payload_too_large")?;
        let request = WebClipInput {
            url: target["url"].as_str().ok_or("browser_unavailable")?.into(),
            html: html.into(),
            kind: input.kind.unwrap_or(WebKind::Template),
            title: input.title,
            form: input.form,
            copy_mode: input.copy_mode,
        };
        client.capture(&request, secret).await.map_err(|e| e.code)
    }
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ClipArgs {
    session_id: String,
    kind: Option<WebKind>,
    title: Option<String>,
    form: Option<FormInput>,
    copy_mode: Option<CopyMode>,
}
fn tool_result(id: Value, result: Result<Value, String>) -> Value {
    let result = match result {
        Ok(value) => json!({"content":[{"type":"text","text":value.to_string()}],"isError":false}),
        Err(code) => {
            json!({"content":[{"type":"text","text":json!({"code":code}).to_string()}],"isError":true})
        }
    };
    json!({"jsonrpc":"2.0","id":id,"result":result})
}
pub async fn serve(
    client: &DmemClient,
    path: PathBuf,
    args: Vec<String>,
    secret: Option<String>,
) -> Result<(), String> {
    let mut wire = Wire::spawn(path, args)?;
    let mut input = BufReader::new(tokio::io::stdin());
    let mut output = tokio::io::stdout();
    let mut initialized = false;
    loop {
        let frame = match crate::read_frame(&mut input).await {
            Ok(Some(value)) => value,
            Ok(None) => break,
            Err(crate::FrameError::TooLarge) => {
                let bytes = format!("{}\n", crate::parse_error());
                output
                    .write_all(bytes.as_bytes())
                    .await
                    .map_err(|_| "internal")?;
                output.flush().await.map_err(|_| "internal")?;
                continue;
            }
            Err(_) => return Err("internal".into()),
        };
        let message: Value = match serde_json::from_slice(&frame) {
            Ok(value) => value,
            Err(_) => {
                output
                    .write_all(format!("{}\n", crate::parse_error()).as_bytes())
                    .await
                    .map_err(|_| "internal")?;
                output.flush().await.map_err(|_| "internal")?;
                continue;
            }
        };
        if !message.is_object()
            || message["jsonrpc"] != "2.0"
            || !message["method"].is_string()
            || message.get("params").is_some_and(|v| !v.is_object())
        {
            output.write_all(format!("{}\n",json!({"jsonrpc":"2.0","id":null,"error":{"code":-32600,"message":"Invalid request"}})).as_bytes()).await.map_err(|_|"internal")?;
            output.flush().await.map_err(|_| "internal")?;
            continue;
        }
        let id = message.get("id").cloned();
        let method = message["method"].as_str().unwrap_or("");
        if id.is_none() {
            if initialized && method == "notifications/initialized" {
                wire.send(&message).await?;
            }
            continue;
        }
        let id = id.unwrap();
        let response = if message["jsonrpc"] != "2.0" || !message.is_object() {
            json!({"jsonrpc":"2.0","id":id,"error":{"code":-32600,"message":"Invalid request"}})
        } else if method == "initialize" {
            let mut params = message["params"].clone();
            params["clientInfo"] = json!({"name":CLIENT,"version":"1"});
            match wire.rpc("initialize", params).await {
                Ok(_) => {
                    initialized = true;
                    crate::handle(client, message.clone())
                        .await
                        .unwrap_or_else(crate::parse_error)
                }
                Err(code) => tool_result(id, Err(code)),
            }
        } else if !initialized {
            tool_result(id, Err("not_initialized".into()))
        } else if method == "tools/list" {
            match wire.catalog().await {
                Ok(result) => json!({"jsonrpc":"2.0","id":id,"result":result}),
                Err(code) => tool_result(id, Err(code)),
            }
        } else if method == "tools/call" {
            let name = message["params"]["name"].as_str().unwrap_or("");
            let args = message["params"]
                .get("arguments")
                .cloned()
                .unwrap_or(json!({}));
            if name == CLIP || name == CLIP_ALIAS {
                tool_result(id, wire.clip(client, args, secret.as_deref()).await)
            } else if crate::tools()
                .as_array()
                .is_some_and(|tools| tools.iter().any(|t| t["name"] == name))
            {
                crate::handle(client, message.clone())
                    .await
                    .unwrap_or_else(crate::parse_error)
            } else {
                if wire.names.is_empty() {
                    let _ = wire.catalog().await?;
                }
                if wire.names.contains(name) {
                    match wire.call(name, args).await {
                        Ok(result) => json!({"jsonrpc":"2.0","id":id,"result":result}),
                        Err(code) => tool_result(id, Err(code)),
                    }
                } else {
                    tool_result(id, Err("unknown_tool".into()))
                }
            }
        } else {
            crate::handle(client, message)
                .await
                .unwrap_or_else(crate::parse_error)
        };
        output
            .write_all(format!("{response}\n").as_bytes())
            .await
            .map_err(|_| "internal")?;
        output.flush().await.map_err(|_| "internal")?;
    }
    let _ = wire.input.shutdown().await;
    if tokio::time::timeout(Duration::from_secs(3), wire.child.wait())
        .await
        .is_err()
    {
        let _ = wire.child.kill().await;
    }
    Ok(())
}

const CAPTURE_JS: &str = r#"JSON.stringify((()=>{
 if(Array.from(document.querySelectorAll('input')).some(e=>e.type==='password'||(e.autocomplete||'').split(/\s+/).some(w=>w.startsWith('cc-'))))return {blocked:true};
 const output=document.implementation.createHTMLDocument(document.title);output.documentElement.lang=document.documentElement.lang||'en-US';
 for(const signal of document.querySelectorAll('link[rel~=license],meta[name=license],meta[name=robots]')){const tag=output.createElement(signal.tagName.toLowerCase());for(const attr of ['rel','href','name','content'])if(signal.hasAttribute(attr))tag.setAttribute(attr,signal.getAttribute(attr));output.head.append(tag);}
 const root=document.querySelector('article,main,[role=document]')||document.body;
 function visible(el){for(let e=el;e&&e!==document.documentElement;e=e.parentElement){const s=getComputedStyle(e);if(['SCRIPT','STYLE','IFRAME','FORM','INPUT','TEXTAREA','SELECT','BUTTON'].includes(e.tagName)||e.hidden||e.getAttribute('aria-hidden')==='true'||s.display==='none'||s.visibility==='hidden'||Number(s.opacity)===0||parseFloat(s.fontSize)===0)return false;const r=e.getBoundingClientRect();if(r.width===0||r.height===0)return false;let bg=e;while(bg&&getComputedStyle(bg).backgroundColor==='rgba(0, 0, 0, 0)')bg=bg.parentElement;if(bg&&s.color===getComputedStyle(bg).backgroundColor)return false;}return true;}
 function text(el){const walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);const parts=[];let node;while(node=walker.nextNode())if(node.parentElement&&visible(node.parentElement))parts.push(node.textContent);return parts.join(' ').replace(/\s+/g,' ').trim();}
 let count=0,size=0;for(const el of root.querySelectorAll('h1,h2,h3,h4,h5,h6,p,li,th,td')){if(++count>2000)break;if(!visible(el))continue;const value=text(el);size+=value.length;if(size>250000)return {blocked:true};if(!value)continue;let tag=el.tagName.toLowerCase();if(tag==='th'||tag==='td'){const table=output.createElement('table'),row=output.createElement('tr'),cell=output.createElement(tag);cell.textContent=value;row.append(cell);table.append(row);output.body.append(table);}else{const node=output.createElement(tag);node.textContent=value;output.body.append(node);}}
 return {url:location.href,html:output.documentElement.outerHTML};
})())"#;
