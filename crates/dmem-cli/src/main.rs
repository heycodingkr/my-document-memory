use clap::{Parser, Subcommand, ValueEnum};
use dmem_client::{DmemClient, contribution_queue_path, recall_path, safe_id, search_path};
use dmem_contracts::{CreateTemplate, RecallQuery, SaveDocument, WebKind, CopyMode, FormInput, WebImportInput};
use serde::de::DeserializeOwned;
use serde_json::{Value, json};
use std::path::{Path, PathBuf};

#[derive(Parser)]
#[command(name = "dmem", about = "My Document Memory client")]
struct Args {
    #[arg(long, env = "DMEM_URL", default_value = "http://127.0.0.1:3847")]
    url: String,
    #[arg(long, env = "DMEM_TOKEN", hide_env_values = true)]
    token: Option<String>,
    #[arg(long, env = "DMEM_ADMIN_TOKEN", hide_env_values = true)]
    admin_token: Option<String>,
    #[arg(long, env = "DMEM_ORIGIN")]
    origin: Option<String>,
    #[command(subcommand)]
    command: Command,
}
#[derive(Clone, Copy, ValueEnum)]
enum Decision {
    Approve,
    Reject,
}
#[derive(Subcommand)]
enum Command {
    /// Forward a public browser MCP on one retained connection and add owned-tab clipping.
    BrowserMcp {
        #[arg(long)]browser_mcp:PathBuf,
        #[arg(long="browser-arg",allow_hyphen_values=true)]browser_arg:Vec<String>,
    },
    /// Search, preview and privately import public document URLs.
    Web { #[command(subcommand)] command: WebCommand },
    Status,
    Templates {
        #[arg(default_value = "")]
        query: String,
    },
    Sources {
        #[arg(default_value = "")]
        query: String,
    },
    Documents {
        #[arg(default_value = "")]
        query: String,
    },
    /// Save a private template from a CreateTemplate JSON file.
    TemplateSave {
        file: PathBuf,
    },
    TemplateShow {
        template_id: String,
    },
    /// Search public templates without a private token.
    PublicTemplates {
        #[arg(default_value = "")]
        query: String,
    },
    PublicTemplate {
        template_id: String,
    },
    Copy {
        template_id: String,
    },
    Import {
        file: PathBuf,
        #[arg(long)]
        title: Option<String>,
    },
    Create {
        template_id: String,
        #[arg(long)]
        title: String,
        #[arg(long)]
        source: Vec<String>,
        #[arg(long)]
        approve_outline: bool,
    },
    Show {
        document_id: String,
    },
    /// Save a revision from JSON containing base_version, title and content.
    Save {
        document_id: String,
        file: PathBuf,
    },
    /// Submit a structure snapshot; explicit rights confirmation is required.
    Contribute {
        template_id: String,
        #[arg(long)]
        author: String,
        #[arg(long)]
        license: String,
        #[arg(long, required = true)]
        rights_confirmed: bool,
    },
    Contributions,
    ContributionCheck {
        contribution_id: String,
    },
    Withdraw {
        contribution_id: String,
    },
    /// Administrator operations require DMEM_ADMIN_TOKEN and an allowed Origin.
    ReviewQueue {
        #[arg(long, default_value = "all", value_parser = ["all", "pending", "approved", "rejected", "withdrawn"])]
        status: String,
        #[arg(long)]
        cursor: Option<String>,
        #[arg(long, default_value_t = 100, value_parser = clap::value_parser!(u16).range(1..=100))]
        limit: u16,
    },
    Review {
        contribution_id: String,
    },
    Decide {
        contribution_id: String,
        #[arg(long, value_enum)]
        decision: Decision,
    },
    Export {
        document_id: String,
        #[arg(long)]
        format: String,
        #[arg(long)]
        output: PathBuf,
    },
    Recall {
        #[arg(value_name = "URL", required_unless_present = "stdin")]
        url: Option<String>,
        #[arg(value_name = "KEYWORD")]
        keywords: Vec<String>,
        #[arg(long)]
        doc_type: Option<String>,
        #[arg(long)]
        locale: Option<String>,
        #[arg(long)]
        provider: Option<String>,
        #[arg(long)]
        kind: Option<String>,
        #[arg(long)]
        scope: Option<String>,
        #[arg(long)]
        limit: Option<u8>,
        #[arg(long)]
        stdin: bool,
    },
}
#[derive(Subcommand)]
enum WebCommand {
    Search { query:String, #[arg(long)]locale:Option<String>, #[arg(long,default_value_t=5)]limit:usize },
    Preview { url:String },
    Import {
        preview_id:String,
        #[arg(long="as",default_value="template",value_parser=["template","reference"])]kind:String,
        #[arg(long)]title:Option<String>,
        #[arg(long,value_parser=["structure_only","full"])]copy_mode:Option<String>,
        #[arg(long,requires_all=["doc_type","locale"])]provider:Option<String>,
        #[arg(long,requires_all=["provider","locale"])]doc_type:Option<String>,
        #[arg(long,requires_all=["provider","doc_type"])]locale:Option<String>,
        #[arg(long,requires_all=["provider","doc_type","locale"])]region:Option<String>,
        #[arg(long,requires_all=["provider","doc_type","locale"])]variant:Option<String>,
    },
    Origin { id:String },
}
fn check(id: &str) -> Result<(), Box<dyn std::error::Error>> {
    if safe_id(id) {
        Ok(())
    } else {
        Err("invalid_input".into())
    }
}
fn input<T: DeserializeOwned>(path: &Path) -> Result<T, Box<dyn std::error::Error>> {
    if std::fs::metadata(path)?.len() > dmem_contracts::MAX_CONTENT as u64 {
        return Err("payload_too_large".into());
    }
    serde_json::from_slice(&std::fs::read(path)?).map_err(|_| "invalid_input".into())
}
#[tokio::main]
async fn main() {
    if let Err(e) = run().await {
        eprintln!("dmem: {e}");
        std::process::exit(1)
    }
}
async fn run() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();
    let is_admin = matches!(
        args.command,
        Command::ReviewQueue { .. } | Command::Review { .. } | Command::Decide { .. }
    );
    let credential = if is_admin {
        args.admin_token
            .filter(|t| !t.is_empty())
            .ok_or("auth_required")?
    } else {
        args.token.unwrap_or_default()
    };
    let mut client = DmemClient::new(&args.url, credential)?;
    if is_admin {
        client = client.with_origin(args.origin.as_deref().unwrap_or(&args.url))?;
    }
    let value: Value = match args.command {
        Command::BrowserMcp{browser_mcp,mut browser_arg}=>{
            if browser_arg.is_empty(){browser_arg.push("--mcp-server".into());}
            return dmem_mcp::bridge::serve(&client,browser_mcp,browser_arg,std::env::var("DMEM_CAPTURE_SECRET").ok()).await.map_err(|code|code.into());
        },
        Command::Web{command}=>match command {
            WebCommand::Search{query,locale,limit}=>client.post("/v1/web/search",&json!({"query":query,"locale":locale,"limit":limit})).await?,
            WebCommand::Preview{url}=>client.post("/v1/web/preview",&json!({"url":url})).await?,
            WebCommand::Origin{id}=>{if !safe_id(&id){return Err("invalid_input".into());}client.get(&format!("/v1/web/origins/{id}")).await?},
            WebCommand::Import{preview_id,kind,title,copy_mode,provider,doc_type,locale,region,variant}=>{
                let form=provider.map(|provider|FormInput{provider,doc_type:doc_type.unwrap_or_default(),locale:locale.unwrap_or_default(),region,variant,page:None});
                let input=WebImportInput{preview_id,kind:if kind=="template"{WebKind::Template}else{WebKind::Reference},title,form,copy_mode:copy_mode.map(|s|if s=="full"{CopyMode::Full}else{CopyMode::StructureOnly})};
                client.post("/v1/web/import",&input).await?
            }
        },
        Command::Status => client.get("/v1/status").await?,
        Command::Templates { query } => client.get(&search_path("templates", &query)).await?,
        Command::Sources { query } => client.get(&search_path("sources", &query)).await?,
        Command::Documents { query } => client.get(&search_path("documents", &query)).await?,
        Command::PublicTemplates { query } => {
            client
                .public_get(&search_path("public/templates", &query))
                .await?
        }
        Command::PublicTemplate { template_id } => {
            check(&template_id)?;
            client
                .public_get(&format!("/v1/public/templates/{template_id}"))
                .await?
        }
        Command::TemplateSave { file } => {
            client
                .post("/v1/templates", &input::<CreateTemplate>(&file)?)
                .await?
        }
        Command::TemplateShow { template_id } => {
            check(&template_id)?;
            client.get(&format!("/v1/templates/{template_id}")).await?
        }
        Command::Copy { template_id } => {
            check(&template_id)?;
            client
                .post(&format!("/v1/templates/{template_id}/copy"), &json!({}))
                .await?
        }
        Command::Import { file, title } => {
            let name = file
                .file_name()
                .and_then(|s| s.to_str())
                .ok_or("invalid_input")?
                .to_owned();
            if std::fs::metadata(&file)?.len() > dmem_contracts::MAX_UPLOAD as u64 {
                return Err("payload_too_large".into());
            }
            client
                .upload(
                    title.unwrap_or_else(|| name.chars().take(120).collect()),
                    name,
                    std::fs::read(file)?,
                )
                .await?
        }
        Command::Create {
            template_id,
            title,
            source,
            approve_outline,
        } => {
            check(&template_id)?;
            for s in &source {
                check(s)?;
            }
            client.post("/v1/documents", &json!({"template_id":template_id,"title":title,"source_ids":source,"outline_approved":approve_outline})).await?
        }
        Command::Show { document_id } => {
            check(&document_id)?;
            client.get(&format!("/v1/documents/{document_id}")).await?
        }
        Command::Save { document_id, file } => {
            check(&document_id)?;
            client
                .put(
                    &format!("/v1/documents/{document_id}"),
                    &input::<SaveDocument>(&file)?,
                )
                .await?
        }
        Command::Contribute {
            template_id,
            author,
            license,
            rights_confirmed,
        } => {
            check(&template_id)?;
            client.post("/v1/me/contributions", &json!({"template_id":template_id,"author":author,"license":license,"rights_confirmed":rights_confirmed})).await?
        }
        Command::Contributions => client.get("/v1/me/contributions").await?,
        Command::ContributionCheck { contribution_id } => {
            check(&contribution_id)?;
            client
                .get(&format!("/v1/me/contributions/{contribution_id}/review"))
                .await?
        }
        Command::Withdraw { contribution_id } => {
            check(&contribution_id)?;
            client
                .post(
                    &format!("/v1/me/contributions/{contribution_id}/withdraw"),
                    &json!({}),
                )
                .await?
        }
        Command::ReviewQueue { status, cursor, limit } => {
            client.get(&contribution_queue_path(&status, cursor.as_deref(), limit)).await?
        },
        Command::Review { contribution_id } => {
            check(&contribution_id)?;
            client
                .get(&format!("/v1/admin/contributions/{contribution_id}/review"))
                .await?
        }
        Command::Decide {
            contribution_id,
            decision,
        } => {
            check(&contribution_id)?;
            let decision = match decision {
                Decision::Approve => "approve",
                Decision::Reject => "reject",
            };
            client
                .post(
                    &format!("/v1/admin/contributions/{contribution_id}/decision"),
                    &json!({"decision":decision}),
                )
                .await?
        }
        Command::Export {
            document_id,
            format,
            output,
        } => {
            check(&document_id)?;
            if !["md", "html", "docx", "pptx"].contains(&format.as_str()) {
                return Err("unsupported_format".into());
            }
            let bytes = client
                .download(&format!("/v1/documents/{document_id}/export/{format}"))
                .await?;
            use std::io::Write;
            let mut f = std::fs::OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(output)?;
            f.write_all(&bytes)?;
            json!({"exported":true,"bytes":bytes.len()})
        }
        Command::Recall {
            url,
            keywords,
            doc_type,
            locale,
            provider,
            kind,
            scope,
            limit,
            stdin,
        } => {
            let q = if stdin {
                if url.is_some()
                    || !keywords.is_empty()
                    || doc_type.is_some()
                    || locale.is_some()
                    || provider.is_some()
                    || kind.is_some()
                    || scope.is_some()
                    || limit.is_some()
                {
                    return Err("invalid_input".into());
                }
                use std::io::Read;
                let mut bytes = Vec::new();
                std::io::stdin().take(8193).read_to_end(&mut bytes)?;
                parse_recall_stdin(&bytes)?
            } else {
                RecallQuery {
                    url: url.ok_or("invalid_input")?,
                    keywords,
                    doc_type,
                    locale,
                    provider,
                    kind,
                    scope,
                    limit,
                }
            };
            client.get(&recall_path(&q)).await?
        }
    };
    println!("{}", serde_json::to_string_pretty(&value)?);
    Ok(())
}

fn parse_recall_stdin(bytes: &[u8]) -> Result<RecallQuery, &'static str> {
    if bytes.len() > 8192 {
        return Err("invalid_input");
    }
    serde_json::from_slice(bytes).map_err(|_| "invalid_input")
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn rv33_recall_help_has_channel_options() {
        let err = match Args::try_parse_from(["dmem", "recall", "--help"]) {
            Err(e) => e.to_string(),
            Ok(_) => panic!("help should exit"),
        };
        for flag in [
            "--doc-type",
            "--locale",
            "--provider",
            "--kind",
            "--scope",
            "--limit",
            "--stdin",
        ] {
            assert!(err.contains(flag), "{flag}");
        }
    }
    #[test]
    fn rv34_stdin_is_bounded_and_rejects_unknown_or_bad_json() {
        assert_eq!(
            parse_recall_stdin(
                br#"{"url":"https://example.org","doc_type":"meeting_minutes","extra":1}"#
            )
            .unwrap_err(),
            "invalid_input"
        );
        assert!(parse_recall_stdin(b"{").is_err());
        assert!(parse_recall_stdin(&vec![b'x'; 8193]).is_err());
        let q = parse_recall_stdin(
            br#"{"url":"https://example.org","doc_type":"meeting_minutes","keywords":["draft"]}"#,
        )
        .unwrap();
        assert_eq!(q.doc_type.as_deref(), Some("meeting_minutes"));
    }
}
