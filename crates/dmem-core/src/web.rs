//! Pure document intake policy. No network, credentials or page execution.
use dmem_contracts::*;
use scraper::{ElementRef, Html, Selector};
use serde::{Deserialize, Serialize};
use std::{
    collections::{BTreeSet, HashMap},
    net::IpAddr,
};
use url::{Host, Url};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum WebPart {
    Heading(String),
    Header(String),
    Paragraph(String),
}
impl WebPart {
    fn value(&self) -> &str {
        match self {
            Self::Heading(s) | Self::Header(s) | Self::Paragraph(s) => s,
        }
    }
    fn value_mut(&mut self) -> &mut String {
        match self {
            Self::Heading(s) | Self::Header(s) | Self::Paragraph(s) => s,
        }
    }
}

pub fn document_parts(blocks: &[Block], slides: &[Slide]) -> Vec<WebPart> {
    let mut parts = Vec::new();
    for block in blocks {
        parts.push(match block {
            Block::Heading { text, .. } => WebPart::Heading(text.clone()),
            _ => WebPart::Paragraph(block.text()),
        });
    }
    for slide in slides {
        parts.push(WebPart::Heading(slide.title.clone()));
        parts.push(WebPart::Paragraph(slide.body.clone()));
    }
    parts
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WebExtract {
    pub title: String,
    pub locale: String,
    pub outline: Vec<String>,
    pub table_headers: Vec<Vec<String>>,
    pub paragraphs: Vec<String>,
    pub parts: Vec<WebPart>,
    pub license: String,
    pub warnings: Vec<String>,
}
impl WebExtract {
    pub fn full_copy_allowed(&self) -> bool {
        ["CC0-1.0", "CC-BY-4.0", "MIT", "Apache-2.0"].contains(&self.license.as_str())
    }
    pub fn text(&self, structure_only: bool) -> String {
        self.parts
            .iter()
            .filter_map(|part| match part {
                WebPart::Heading(s) => Some(format!("## {s}")),
                WebPart::Header(s) => Some(s.clone()),
                WebPart::Paragraph(s) if !structure_only => Some(s.clone()),
                _ => None,
            })
            .collect::<Vec<_>>()
            .join("\n")
    }
    pub fn sanitize(mut self) -> Result<Self, Fault> {
        let mut removed = false;
        for values in [&mut self.outline, &mut self.paragraphs] {
            values.retain(|s| {
                let keep = !crate::review::contains_injection(s);
                removed |= !keep;
                keep
            });
            for s in values {
                *s = clean(s);
            }
        }
        for row in &mut self.table_headers {
            row.retain(|s| !crate::review::contains_injection(s));
            for s in row {
                *s = clean(s);
            }
        }
        self.parts.retain(|part| {
            let keep = !crate::review::contains_injection(part.value());
            removed |= !keep;
            keep
        });
        for part in &mut self.parts {
            *part.value_mut() = clean(part.value());
        }
        self.title = clean(&self.title).chars().take(120).collect();
        if crate::review::contains_injection(&self.title) {
            self.title = "Imported document".into();
            removed = true;
        }
        let content = serde_json::to_string(&self).map_err(|_| Fault::InvalidInput)?;
        if content.len() > MAX_CONTENT {
            return Err(Fault::PayloadTooLarge);
        }
        if std::iter::once(&self.title)
            .chain(self.outline.iter())
            .chain(self.paragraphs.iter())
            .chain(self.table_headers.iter().flatten())
            .map(String::as_str)
            .chain(self.parts.iter().map(WebPart::value))
            .any(crate::review::contains_secret)
        {
            return Err(Fault::FetchBlocked("secret"));
        }
        if removed {
            self.warnings.push("injection_removed".into());
        }
        if self.outline.is_empty() && self.paragraphs.is_empty() && self.table_headers.is_empty() {
            return Err(Fault::ExtractEmpty("no_visible_content"));
        }
        self.outline.truncate(12);
        self.warnings.sort();
        self.warnings.dedup();
        Ok(self)
    }
}
pub fn clean(value: &str) -> String {
    value.chars().filter(|c| !matches!(*c, '\u{00ad}'|'\u{180e}'|'\u{200b}'..='\u{200f}'|'\u{202a}'..='\u{202e}'|'\u{2060}'|'\u{2066}'..='\u{2069}'|'\u{feff}'))
        .collect::<String>().split_whitespace().collect::<Vec<_>>().join(" ")
}
fn sel(s: &str) -> Selector {
    Selector::parse(s).expect("static selector")
}
fn hidden_style(style: &str) -> bool {
    let pairs: HashMap<_, _> = style
        .split(';')
        .filter_map(|s| s.split_once(':'))
        .map(|(k, v)| {
            (
                k.trim().to_lowercase(),
                v.trim()
                    .to_lowercase()
                    .replace("!important", "")
                    .trim()
                    .to_string(),
            )
        })
        .collect();
    let value = |key: &str| pairs.get(key).map(String::as_str).unwrap_or("");
    let zero = |v: &str| ["0", "0px", "0em", "0rem", "0%", "0.0", "0.0px"].contains(&v);
    value("display") == "none"
        || ["hidden", "collapse"].contains(&value("visibility"))
        || zero(value("opacity"))
        || zero(value("font-size"))
        || zero(value("height"))
        || zero(value("width"))
        || value("color") == "transparent"
        || (!value("color").is_empty()
            && (value("color") == value("background-color")
                || value("color") == value("background")))
}
fn hidden(el: ElementRef<'_>, classes: &BTreeSet<String>, ids: &BTreeSet<String>) -> bool {
    el.ancestors()
        .filter_map(ElementRef::wrap)
        .chain(std::iter::once(el))
        .any(|e| {
            let v = e.value();
            [
                "script", "style", "iframe", "object", "embed", "form", "input", "textarea",
                "select", "button", "noscript", "template",
            ]
            .contains(&v.name())
                || v.attr("hidden").is_some()
                || v.attr("aria-hidden") == Some("true")
                || hidden_style(v.attr("style").unwrap_or(""))
                || v.classes().any(|c| classes.contains(c))
                || v.id().is_some_and(|id| ids.contains(id))
        })
}
fn visible_text(el: ElementRef<'_>, classes: &BTreeSet<String>, ids: &BTreeSet<String>) -> String {
    clean(
        &el.descendants()
            .filter(|n| n.value().is_text())
            .filter(|n| {
                n.ancestors()
                    .filter_map(ElementRef::wrap)
                    .all(|e| !hidden(e, classes, ids))
            })
            .filter_map(|n| n.value().as_text().map(|s| s.to_string()))
            .collect::<Vec<_>>()
            .join(" "),
    )
}
fn license(value: &str) -> String {
    match value.trim() {
        "CC0-1.0" | "CC-BY-4.0" | "MIT" | "Apache-2.0" => return value.trim().into(),
        _ => {}
    }
    if let Ok(u) = Url::parse(value) {
        if u.scheme() == "https"
            && u.host_str() == Some("creativecommons.org")
            && u.query().is_none()
        {
            return match u.path().trim_end_matches('/') {
                "/publicdomain/zero/1.0" => "CC0-1.0",
                "/licenses/by/4.0" => "CC-BY-4.0",
                _ => "proprietary-structure-only",
            }
            .into();
        }
    }
    "proprietary-structure-only".into()
}
pub fn parse_html(html: &str) -> Result<WebExtract, Fault> {
    if html.len() > WEB_MAX_BYTES {
        return Err(Fault::PayloadTooLarge);
    }
    let doc = Html::parse_document(html);
    if doc.tree.nodes().take(20001).count() > 20000
        || doc
            .tree
            .nodes()
            .any(|n| n.ancestors().take(65).count() > 64)
    {
        return Err(Fault::PayloadTooLarge);
    }
    for input in doc.select(&sel("input")) {
        let v = input.value();
        if v.attr("type")
            .is_some_and(|t| t.eq_ignore_ascii_case("password"))
            || v.attr("autocomplete")
                .is_some_and(|a| a.split_whitespace().any(|word| word.starts_with("cc-")))
        {
            return Err(Fault::FetchBlocked("login_required"));
        }
    }
    if doc
        .select(&sel("meta[name=robots],meta[name=googlebot]"))
        .any(|e| {
            e.value()
                .attr("content")
                .unwrap_or("")
                .to_lowercase()
                .split([',', ' '])
                .any(|s| s == "noai")
        })
    {
        return Err(Fault::FetchBlocked("signal_noai"));
    }
    let mut classes = BTreeSet::new();
    let mut ids = BTreeSet::new();
    for style in doc.select(&sel("style")) {
        let css = style.text().collect::<String>();
        for rule in css.split('}') {
            if let Some((selector, declarations)) = rule.split_once('{') {
                if hidden_style(declarations) {
                    for word in
                        selector.split(|c: char| !(c.is_alphanumeric() || ".#_-".contains(c)))
                    {
                        if let Some(class) = word.strip_prefix('.') {
                            classes.insert(class.to_string());
                        }
                        if let Some(id) = word.strip_prefix('#') {
                            ids.insert(id.to_string());
                        }
                    }
                }
            }
        }
    }
    let title = doc
        .select(&sel("title"))
        .next()
        .map(|e| clean(&e.text().collect::<String>()))
        .filter(|s| !s.is_empty())
        .unwrap_or_else(|| "Imported document".into());
    let locale = doc
        .select(&sel("html"))
        .next()
        .and_then(|e| e.value().attr("lang"))
        .unwrap_or("en-US")
        .to_string();
    let mut page = WebExtract {
        title,
        locale,
        outline: vec![],
        table_headers: vec![],
        paragraphs: vec![],
        parts: vec![],
        license: "unknown".into(),
        warnings: vec!["styles_approximated".into()],
    };
    let mut licenses: Vec<String> = doc
        .select(&sel("link[rel~=license],meta[name=license]"))
        .map(|signal| {
            license(
                signal
                    .value()
                    .attr("href")
                    .or_else(|| signal.value().attr("content"))
                    .unwrap_or(""),
            )
        })
        .collect();
    fn json_licenses(value: &serde_json::Value, licenses: &mut Vec<String>) {
        match value {
            serde_json::Value::Object(object) => {
                if let Some(value) = object
                    .get("license")
                    .and_then(|v| v.as_str().or_else(|| v["@id"].as_str()))
                {
                    licenses.push(license(value));
                }
                for (key, value) in object {
                    if key != "license" {
                        json_licenses(value, licenses);
                    }
                }
            }
            serde_json::Value::Array(values) => {
                for value in values {
                    json_licenses(value, licenses)
                }
            }
            _ => {}
        }
    }
    for script in doc.select(&sel("script[type='application/ld+json']")) {
        if let Ok(value) =
            serde_json::from_str::<serde_json::Value>(&script.text().collect::<String>())
        {
            json_licenses(&value, &mut licenses);
        }
    }
    for detected in licenses {
        if page.license == "unknown" {
            page.license = detected;
        } else if page.license != detected {
            page.license = "proprietary-structure-only".into();
        }
    }
    for element in doc.select(&sel("h1,h2,h3,h4,h5,h6,p,li,th,td")) {
        if hidden(element, &classes, &ids) {
            page.warnings.push("hidden_text_removed".into());
            continue;
        }
        let text = visible_text(element, &classes, &ids);
        if text.is_empty() {
            continue;
        }
        match element.value().name() {
            "h1" | "h2" | "h3" | "h4" | "h5" | "h6" => {
                page.outline.push(text.chars().take(60).collect());
                page.parts.push(WebPart::Heading(text));
            }
            "th" => page.parts.push(WebPart::Header(text)),
            _ => {
                page.paragraphs.push(text.clone());
                page.parts.push(WebPart::Paragraph(text));
            }
        }
    }
    for row in doc.select(&sel("tr")) {
        let headers: Vec<_> = row
            .select(&sel("th"))
            .filter(|e| !hidden(*e, &classes, &ids))
            .map(|e| visible_text(e, &classes, &ids))
            .filter(|s| !s.is_empty())
            .collect();
        if !headers.is_empty() {
            page.table_headers.push(headers);
        }
    }
    if page.outline.is_empty() && page.paragraphs.is_empty() && page.table_headers.is_empty() {
        if let Some(body) = doc.select(&sel("body")).next() {
            let text = visible_text(body, &classes, &ids);
            if !text.is_empty() {
                page.paragraphs.push(text.clone());
                page.parts.push(WebPart::Paragraph(text));
            }
        }
    }
    if html
        .chars()
        .any(|c| matches!(c,'\u{200b}'..='\u{200f}'|'\u{202a}'..='\u{202e}'))
    {
        page.warnings.push("hidden_text_removed".into());
    }
    page.sanitize()
}

pub fn safe_fetch_url(input: &str) -> Result<Url, Fault> {
    if input.len() > 2048 || input.chars().any(char::is_control) {
        return Err(Fault::InvalidInput);
    }
    let mut url = Url::parse(input).map_err(|_| Fault::FetchBlocked("url"))?;
    if url.scheme() != "https" {
        return Err(Fault::FetchBlocked("scheme"));
    }
    if !url.username().is_empty() || url.password().is_some() {
        return Err(Fault::FetchBlocked("credentials"));
    }
    if url.port_or_known_default() != Some(443) {
        return Err(Fault::FetchBlocked("port"));
    }
    let host = match url.host() {
        Some(Host::Domain(h)) => h,
        _ => return Err(Fault::FetchBlocked("private_address")),
    };
    if !host.contains('.')
        || ["localhost", "local", "internal", "test", "invalid", "onion"]
            .iter()
            .any(|suffix| host == *suffix || host.ends_with(&format!(".{suffix}")))
    {
        return Err(Fault::FetchBlocked("private_address"));
    }
    url.set_query(None);
    url.set_fragment(None);
    Ok(url)
}
pub fn public_ip(ip: IpAddr) -> bool {
    match ip {
        IpAddr::V4(v) => {
            let [a, b, c, d] = v.octets();
            !matches!(a, 0 | 10 | 127 | 224..=255)
                && !(a == 100 && (64..=127).contains(&b))
                && !(a == 169 && b == 254)
                && !(a == 172 && (16..=31).contains(&b))
                && !(a == 192 && (b == 168 || b == 0 || b == 2 || b == 88 && c == 99))
                && !(a == 198 && (b == 18 || b == 19 || b == 51 && c == 100))
                && !(a == 203 && b == 0 && c == 113)
                && [a, b, c, d] != [255, 255, 255, 255]
        }
        IpAddr::V6(v) => {
            let bytes = v.octets();
            if let Some(v4) = v.to_ipv4_mapped() {
                return public_ip(IpAddr::V4(v4));
            }
            if bytes[..12] == [0, 100, 255, 155, 0, 0, 0, 0, 0, 0, 0, 0] {
                return public_ip(IpAddr::V4(std::net::Ipv4Addr::new(
                    bytes[12], bytes[13], bytes[14], bytes[15],
                )));
            }
            // Only ordinary global unicast; exclude transition/special-purpose prefixes.
            (bytes[0] & 0xe0) == 0x20
                && !(bytes[0] == 0x20 && bytes[1] == 0x01 && bytes[2] == 0x0d && bytes[3] == 0xb8)
                && !(bytes[0] == 0x20 && bytes[1] == 0x01 && bytes[2] < 2)
                && !(bytes[0] == 0x20 && bytes[1] == 0x02)
        }
    }
}
