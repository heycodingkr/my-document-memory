use dmem_contracts::*;
use percent_encoding::percent_decode_str;
use serde_json::Value;
use unicode_normalization::UnicodeNormalization;
use url::{Host, Url};

pub fn vocabulary() -> Value {
    serde_json::json!({
     "doc_types":serde_json::from_str::<Value>(include_str!("../../../contracts/vocab/doc_types.json")).expect("bundled vocabulary"),
     "regions":serde_json::from_str::<Value>(include_str!("../../../contracts/vocab/regions.json")).expect("bundled regions")
    })
}
pub fn provider_family(p: Provider) -> Family {
    match p {
        Provider::GoogleSlides | Provider::Pptx => Family::Deck,
        Provider::GoogleSheets | Provider::Xlsx => Family::Sheet,
        _ => Family::Document,
    }
}
fn key(s: &str) -> String {
    s.nfkc()
        .collect::<String>()
        .to_lowercase()
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
}
pub fn normalize_form(i: FormInput) -> Result<Form, Fault> {
    let provider: Provider = serde_json::from_value(Value::String(i.provider))
        .map_err(|_| Fault::InvalidForm("provider_unknown"))?;
    let vocab = vocabulary();
    let input = key(&i.doc_type);
    let mut doc = None;
    let mut implied = None;
    for item in vocab["doc_types"]["items"].as_array().expect("items") {
        let id = item["id"].as_str().expect("id");
        if input == id {
            doc = Some(item);
            break;
        }
        for a in item["aliases"].as_array().expect("aliases") {
            if key(a["value"].as_str().expect("alias")) == input {
                doc = Some(item);
                implied = a["variant"].as_str().map(str::to_owned);
                break;
            }
        }
        if doc.is_some() {
            break;
        }
    }
    let doc = doc.ok_or(Fault::InvalidForm("doc_type_unknown"))?;
    let family = provider_family(provider);
    if !doc["family"].is_null() && serde_json::to_value(family).ok() != Some(doc["family"].clone())
    {
        return Err(Fault::InvalidForm("family_mismatch"));
    }
    let parts = i.locale.replace('_', "-").to_ascii_lowercase();
    let pieces: Vec<_> = parts.split('-').collect();
    if pieces.is_empty() || pieces.len() > 2 {
        return Err(Fault::InvalidForm("locale_unknown"));
    }
    let lang = pieces[0];
    let locale = if pieces.len() == 2 {
        format!("{}-{}", lang, pieces[1].to_ascii_uppercase())
    } else {
        lang.into()
    };
    let supported = vocab["regions"]["locales"].as_array().expect("locales");
    if !supported.iter().any(|l| {
        let s = l.as_str().unwrap_or("");
        s == locale || (pieces.len() == 1 && s.starts_with(&format!("{lang}-")))
    }) {
        return Err(Fault::InvalidForm("locale_unknown"));
    }
    let region = i
        .region
        .map(|s| s.to_ascii_uppercase())
        .or_else(|| locale.split_once('-').map(|(_, r)| r.to_owned()));
    if region.as_ref().is_some_and(|r| {
        !vocab["regions"]["regions"]
            .as_array()
            .expect("regions")
            .iter()
            .any(|v| v.as_str() == Some(r))
    }) {
        return Err(Fault::InvalidForm("locale_unknown"));
    }
    let variant = i.variant.or(implied);
    if variant.as_ref().is_some_and(|v| {
        v.is_empty()
            || v.len() > 32
            || !v
                .bytes()
                .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b == b'_')
    }) {
        return Err(Fault::InvalidForm("variant_invalid"));
    }
    if let Some(p) = &i.page {
        if !["A4", "A3", "A5", "Letter", "Legal", "16:9", "4:3", "custom"]
            .contains(&p.size.as_str())
            || !["portrait", "landscape"].contains(&p.orientation.as_str())
            || p.margins_mm.is_some_and(|m| m.iter().any(|v| *v > 100))
        {
            return Err(Fault::InvalidForm("page_invalid"));
        }
        if (family == Family::Deck && !["16:9", "4:3", "custom"].contains(&p.size.as_str()))
            || (family == Family::Document && ["16:9", "4:3"].contains(&p.size.as_str()))
        {
            return Err(Fault::InvalidForm("page_invalid"));
        }
    }
    Ok(Form {
        provider,
        family,
        doc_type: doc["id"].as_str().unwrap().into(),
        locale,
        region,
        variant,
        page: i.page,
    })
}

#[derive(Debug, Clone, PartialEq)]
pub struct CanonicalUrl {
    pub pattern: String,
    pub provider: Provider,
}
pub fn normalize_url(input: &str) -> Result<CanonicalUrl, Fault> {
    let err = |r| Fault::UrlRejected(r);
    if input.chars().count() > 2048 {
        return Err(err("too_long"));
    }
    let normalized: String = input.nfkc().collect();
    let url = Url::parse(&normalized).map_err(|_| err("unclassifiable"))?;
    if url.scheme() != "https" {
        return Err(err("scheme_not_allowed"));
    }
    if !url.username().is_empty()
        || url.password().is_some()
        || normalized
            .split("://")
            .nth(1)
            .and_then(|s| s.split('/').next())
            .is_some_and(|s| s.contains('@'))
    {
        return Err(err("userinfo_not_allowed"));
    }
    let host = match url.host() {
        Some(Host::Domain(h)) => h.trim_end_matches('.').to_ascii_lowercase(),
        _ => return Err(err("host_not_allowed")),
    };
    if !host.contains('.')
        || host == "localhost"
        || [
            ".localhost",
            ".local",
            ".internal",
            ".lan",
            ".home",
            ".localdomain",
        ]
        .iter()
        .any(|s| host.ends_with(s))
        || host == "metadata.google.internal"
        || url.port().is_some()
    {
        return Err(err("host_not_allowed"));
    }
    let decoded = percent_decode_str(url.path())
        .decode_utf8()
        .map_err(|_| err("unclassifiable"))?;
    let path: String = decoded.nfkc().collect();
    let mut parts: Vec<String> = path
        .split('/')
        .filter(|s| !s.is_empty())
        .map(str::to_owned)
        .collect();
    let mut provider = Provider::Other;
    if host == "docs.google.com" && !parts.is_empty() {
        provider = match parts[0].as_str() {
            "document" => Provider::GoogleDocs,
            "presentation" => Provider::GoogleSlides,
            "spreadsheets" => Provider::GoogleSheets,
            _ => Provider::Other,
        };
        if provider != Provider::Other {
            if parts.get(1).map(String::as_str) == Some("u")
                && parts
                    .get(2)
                    .is_some_and(|s| s.bytes().all(|b| b.is_ascii_digit()))
            {
                parts.drain(1..3);
            }
            if parts.get(1).map(String::as_str) == Some("d") && parts.get(2).is_some() {
                parts[2] = ":id".into();
                parts.truncate(4);
                if parts.len() == 4
                    && !["edit", "view", "preview", "copy", "export", "template"]
                        .contains(&parts[3].as_str())
                {
                    parts.truncate(3)
                }
            } else {
                parts.truncate(1);
            }
        }
    } else if host == "notion.so" || host == "www.notion.so" || host.ends_with(".notion.site") {
        provider = Provider::Notion;
        if parts.last().is_some_and(|s| {
            let tail = s.rsplit('-').next().unwrap_or("");
            tail.len() == 32 && tail.bytes().all(|b| b.is_ascii_hexdigit())
        }) {
            parts = vec![":id".into()]
        }
    } else if let Some(last) = parts.last() {
        provider = match last
            .rsplit('.')
            .next()
            .unwrap_or("")
            .to_ascii_lowercase()
            .as_str()
        {
            "docx" => Provider::Docx,
            "pptx" => Provider::Pptx,
            "xlsx" => Provider::Xlsx,
            "pdf" => Provider::Pdf,
            "md" | "markdown" => Provider::Markdown,
            "txt" => Provider::Txt,
            _ => Provider::Other,
        };
    }
    // Capability tokens have no reliable length/alphabet. Only retain known route words.
    let on = |domain: &str| host == domain || host.ends_with(&format!(".{domain}"));
    if host == "drive.google.com" {
        if parts.first().map(String::as_str) == Some("file")
            && parts.get(1).map(String::as_str) == Some("d")
            && parts.len() >= 3
        {
            parts = vec!["file".into(), "d".into(), ":id".into()];
        } else if parts.first().map(String::as_str) == Some("drive")
            && parts.get(1).map(String::as_str) == Some("folders")
        {
            parts = vec!["drive".into(), "folders".into(), ":id".into()];
        } else {
            parts.clear();
        }
    } else if on("figma.com") || on("canva.com") {
        if parts
            .first()
            .is_some_and(|p| ["file", "design", "proto", "board"].contains(&p.as_str()))
            && parts.len() >= 2
        {
            parts.truncate(2);
            parts[1] = ":id".into();
        } else {
            parts.clear();
        }
    } else if on("dropbox.com") {
        if parts.first().map(String::as_str) == Some("s") && parts.len() >= 2 {
            parts = vec!["s".into(), ":id".into()];
        } else if parts.first().map(String::as_str) == Some("scl")
            && parts.get(1).map(String::as_str) == Some("fi")
            && parts.len() >= 3
        {
            parts = vec!["scl".into(), "fi".into(), ":id".into()];
        } else {
            parts.clear();
        }
    } else if host == "onedrive.live.com"
        || host == "1drv.ms"
        || on("sharepoint.com")
        || (host == "docs.google.com" && provider == Provider::Other)
        || (provider == Provider::Notion && parts != [":id"])
    {
        parts.clear();
    }
    let mut out = Vec::new();
    for s in parts.into_iter().take(8) {
        if s == ":id" {
            out.push(s);
            continue;
        }
        if s.contains('@') && s.contains('.') {
            return Err(err("pii_in_url"));
        }
        if s.starts_with('@') {
            out.push(":handle".into());
            continue;
        }
        let bytes = s.as_bytes();
        let uuid = s.len() == 36
            && [8, 13, 18, 23].iter().all(|n| bytes[*n] == b'-')
            && s.replace('-', "").bytes().all(|b| b.is_ascii_hexdigit());
        let suffix = s.rsplit_once('-').is_some_and(|(_, t)| {
            (t.len() >= 8 && t.bytes().all(|b| b.is_ascii_hexdigit()))
                || (t.len() >= 4 && t.bytes().all(|b| b.is_ascii_digit()))
        });
        let dynamic = bytes.iter().all(u8::is_ascii_digit)
            || (s.len() >= 16 && bytes.iter().all(u8::is_ascii_hexdigit))
            || uuid
            || suffix
            || (s.len() >= 20
                && bytes
                    .iter()
                    .all(|b| b.is_ascii_alphanumeric() || *b == b'_' || *b == b'-')
                && bytes.iter().any(u8::is_ascii_digit)
                && bytes.iter().any(u8::is_ascii_alphabetic));
        if dynamic {
            out.push(":id".into())
        } else if s.chars().count() <= 40
            && s.chars().all(|c| c.is_alphanumeric() || "._~-".contains(c))
        {
            out.push(s)
        } else {
            break;
        }
    }
    Ok(CanonicalUrl {
        pattern: format!("{host}/{}", out.join("/")),
        provider,
    })
}
