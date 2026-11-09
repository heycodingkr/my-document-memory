use dmem_contracts::*;
use dmem_core::{export, extract, normalize_form, normalize_url};
#[test]
fn provider_ids_and_queries_never_survive_projection() {
    for url in [
        "https://docs.google.com/document/d/PRIVATE_12345/edit?resourcekey=SECRET",
        "https://docs.google.com/document/u/2/d/ANOTHER_ID/edit#private",
    ] {
        let c = normalize_url(url).unwrap();
        assert_eq!(c.pattern, "docs.google.com/document/d/:id/edit");
        assert_eq!(c.provider, Provider::GoogleDocs);
    }
    assert_eq!(
        normalize_url(
            "https://www.notion.so/workspace/Private-0123456789abcdef0123456789abcdef?pvs=4"
        )
        .unwrap()
        .pattern,
        "www.notion.so/:id"
    );
    assert_eq!(
        normalize_url("https://example.com/people/123/profile")
            .unwrap()
            .pattern,
        "example.com/people/:id/profile"
    );
}
#[test]
fn rejects_unsafe_urls_with_fixed_errors() {
    for (input, reason) in [
        ("http://example.com/", "scheme_not_allowed"),
        ("https://user:secret@example.com/", "userinfo_not_allowed"),
        ("https://127.0.0.1/", "host_not_allowed"),
        ("https://0x7f000001/", "host_not_allowed"),
        ("https://localhost/", "host_not_allowed"),
        ("https://example.com:8443/", "host_not_allowed"),
        ("https://example.com/jane.doe@corp.test/", "pii_in_url"),
    ] {
        assert_eq!(
            normalize_url(input).unwrap_err(),
            Fault::UrlRejected(reason)
        );
    }
}
#[test]
fn aliases_locale_and_family_are_normalized() {
    let input = FormInput {
        provider: "docx".into(),
        doc_type: "履歴書".into(),
        locale: "KO_kr".into(),
        region: None,
        variant: None,
        page: None,
    };
    let f = normalize_form(input.clone()).unwrap();
    assert_eq!(
        (f.doc_type.as_str(), f.locale.as_str(), f.variant.as_deref()),
        ("resume", "ko-KR", Some("jp_rirekisho"))
    );
    let mut bad = input;
    bad.provider = "google_slides".into();
    assert_eq!(
        normalize_form(bad).unwrap_err(),
        Fault::InvalidForm("family_mismatch")
    );
}
#[test]
fn office_round_trip_and_html_escaping() {
    let c = Content {
        blocks: vec![
            Block::Heading {
                text: "회의록 <script>".into(),
                level: 1,
            },
            Block::Table {
                rows: vec![vec!["항목 & 값".into(), "결정".into()]],
            },
            Block::Paragraph {
                text: "원문 보존".into(),
            },
        ],
        slides: vec![],
    };
    let html =
        String::from_utf8(export("제목", Family::Document, &c, "html").unwrap().bytes).unwrap();
    assert!(!html.contains("<script>"));
    assert!(html.contains("&lt;script&gt;"));
    let docx = export("제목", Family::Document, &c, "docx").unwrap();
    let doc = extract("fixture.docx", &docx.bytes).unwrap();
    assert!(doc.blocks.iter().any(|b| matches!(b, Block::Table { .. })));
    assert!(doc.spans.iter().any(|s| s.text.contains("항목 & 값")));
    let deck = Content {
        blocks: vec![],
        slides: vec![Slide {
            title: "문제".into(),
            body: "고객 & 요청".into(),
            citations: vec![],
        }],
    };
    let pptx = export("덱", Family::Deck, &deck, "pptx").unwrap();
    let parsed = extract("fixture.pptx", &pptx.bytes).unwrap();
    assert_eq!(parsed.slides.len(), 1);
    assert_eq!(parsed.slides[0].title, "문제");
    assert!(parsed.slides[0].body.contains("고객 & 요청"));
}
#[test]
fn invalid_files_and_unknown_fields() {
    assert_eq!(
        extract("empty.txt", b"  ").unwrap_err(),
        Fault::ExtractEmpty("no_text")
    );
    assert_eq!(
        extract("bad.docx", b"not a zip").unwrap_err(),
        Fault::InvalidInput
    );
    assert_eq!(
        extract("scan.pdf", b"%PDF").unwrap_err(),
        Fault::UnsupportedFormat
    );
    assert!(
        serde_json::from_value::<SaveDocument>(
            serde_json::json!({"base_version":1,"title":"t","content":{},"owner":"victim"})
        )
        .is_err()
    );
}

#[test]
fn capability_hosts_never_keep_opaque_share_ids() {
    for input in [
        "https://drive.google.com/file/d/SUPER_SECRET_ALPHA_TOKEN/view?resourcekey=PRIVATE",
        "https://www.dropbox.com/s/PRIVATEALPHATOKEN/Private-Plan.docx?dl=0",
        "https://www.figma.com/file/PRIVATEALPHATOKEN/Private-Plan",
        "https://www.canva.com/design/PRIVATEALPHATOKEN/view",
    ] {
        let pattern = normalize_url(input).unwrap().pattern;
        assert!(
            !pattern.contains("PRIVATE") && !pattern.contains("SECRET"),
            "{pattern}"
        );
    }
}

#[test]
fn markdown_tables_have_a_header_separator() {
    let content = Content {
        blocks: vec![Block::Table {
            rows: vec![
                vec!["항목".into(), "결과".into()],
                vec!["일정".into(), "확정".into()],
            ],
        }],
        slides: vec![],
    };
    let text = String::from_utf8(
        export("제목", Family::Document, &content, "md")
            .unwrap()
            .bytes,
    )
    .unwrap();
    assert!(text.contains("| 항목 | 결과 |\n| --- | --- |\n| 일정 | 확정 |"));
}

#[test]
fn independent_pptx_fixture_preserves_presentation_order() {
    use std::io::{Cursor, Write};
    let mut z = zip::ZipWriter::new(Cursor::new(Vec::new()));
    let options = zip::write::SimpleFileOptions::default();
    for (name, text) in [
        (
            "ppt/presentation.xml",
            "<p:presentation xmlns:p='urn:p' xmlns:r='urn:r'><p:sldIdLst><p:sldId id='256' r:id='second'/><p:sldId id='257' r:id='first'/></p:sldIdLst></p:presentation>",
        ),
        (
            "ppt/_rels/presentation.xml.rels",
            "<Relationships><Relationship Id='first' Target='slides/slide1.xml'/><Relationship Id='second' Target='slides/slide9.xml'/></Relationships>",
        ),
        (
            "ppt/slides/slide1.xml",
            "<p:sld xmlns:p='urn:p' xmlns:a='urn:a'><a:p><a:r><a:t>마지막 장</a:t></a:r></a:p></p:sld>",
        ),
        (
            "ppt/slides/slide9.xml",
            "<p:sld xmlns:p='urn:p' xmlns:a='urn:a'><a:p><a:r><a:t>첫 장</a:t></a:r></a:p></p:sld>",
        ),
    ] {
        z.start_file(name, options).unwrap();
        z.write_all(text.as_bytes()).unwrap();
    }
    let fixture = z.finish().unwrap().into_inner();
    let parsed = extract("independent.pptx", &fixture).unwrap();
    assert_eq!(
        parsed
            .slides
            .iter()
            .map(|s| s.title.as_str())
            .collect::<Vec<_>>(),
        ["첫 장", "마지막 장"]
    );
}

#[test]
fn zip_expansion_and_entity_declarations_are_bounded() {
    use std::io::{Cursor, Write};
    let mut z = zip::ZipWriter::new(Cursor::new(Vec::new()));
    z.start_file(
        "word/document.xml",
        zip::write::SimpleFileOptions::default()
            .compression_method(zip::CompressionMethod::Deflated),
    )
    .unwrap();
    z.write_all(&vec![b'x'; 6 * 1024 * 1024]).unwrap();
    assert_eq!(
        extract("bomb.docx", &z.finish().unwrap().into_inner()).unwrap_err(),
        Fault::PayloadTooLarge
    );
    let mut z = zip::ZipWriter::new(Cursor::new(Vec::new()));
    z.start_file(
        "word/document.xml",
        zip::write::SimpleFileOptions::default(),
    )
    .unwrap();
    z.write_all(br#"<!DOCTYPE document [<!ENTITY ext SYSTEM "file:///SENTINEL">]><document><p><t>&ext;</t></p></document>"#).unwrap();
    assert_eq!(
        extract("entity.docx", &z.finish().unwrap().into_inner()).unwrap_err(),
        Fault::InvalidInput
    );
}
