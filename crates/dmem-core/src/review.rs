//! Deterministic checks for public structure snapshots; no model, I/O or publication.
use dmem_contracts::{Template, Visibility};
use regex::Regex;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{collections::BTreeSet, sync::OnceLock};
use unicode_normalization::UnicodeNormalization;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub struct ReviewFinding {
    pub rule: String,
    pub field: String,
    pub code: String,
    pub reason: String,
    pub action: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReviewStage {
    pub rule: String,
    pub label: String,
    pub status: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReviewReport {
    pub schema_version: u32,
    pub policy: String,
    pub contribution_id: String,
    pub snapshot_version: u32,
    pub snapshot_hash: String,
    pub verdict: String,
    pub reasons: Vec<String>,
    pub findings: Vec<ReviewFinding>,
    pub stages: Vec<ReviewStage>,
    pub decision: Option<String>,
    pub decided_at: Option<u64>,
}
fn normalized(value: &str) -> String {
    value
        .nfkc()
        .filter(|c| {
            !matches!(*c,
                '\u{00ad}' | '\u{180e}' | '\u{200b}'..='\u{200f}' | '\u{202a}'..='\u{202e}' |
                '\u{2060}' | '\u{2066}'..='\u{2069}' | '\u{feff}'
            )
        })
        .collect()
}
fn canonical(value: &str) -> String {
    normalized(value)
        .to_lowercase()
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
}
fn structure_key(t: &Template) -> String {
    let mut parts = vec![
        "dmem-contribution-review-v1".to_string(),
        format!("{:?}", t.form.family),
        format!("{:?}", t.form.provider),
        canonical(&t.form.doc_type),
        canonical(&t.form.locale),
        canonical(t.form.region.as_deref().unwrap_or("")),
        canonical(t.form.variant.as_deref().unwrap_or("")),
    ];
    parts.extend(t.sections.iter().map(|s| canonical(s)));
    parts.join("\n")
}
fn patterns() -> &'static Vec<(&'static str, &'static str, Regex)> {
    static PATTERNS: OnceLock<Vec<(&str, &str, Regex)>> = OnceLock::new();
    PATTERNS.get_or_init(|| [
        ("secret", "api_key_sk", r"(?i)\bsk-[a-z0-9_-]{16,}"),
        ("secret", "aws_access_key", r"\bAKIA[A-Z0-9]{16}\b"),
        ("secret", "github_token", r"\bgh[pousr]_[A-Za-z0-9]{36}\b"),
        ("secret", "jwt", r"\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),
        ("secret", "bearer_token", r"(?i)\bbearer\s+[a-z0-9._~+/=-]{8,}"),
        ("secret", "private_key", r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----"),
        ("secret", "slack_token", r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
        ("secret", "google_api_key", r"\bAIza[0-9A-Za-z_-]{35}\b"),
        ("personal_data", "email", r"(?i)[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}"),
        ("personal_data", "phone", r"(?:\+1[ .-]?)?\(?[0-9]{3}\)?[ .-][0-9]{3}[ .-][0-9]{4}\b|\b0[19]0[-. ]?[0-9]{4}[-. ]?[0-9]{4}\b|\b01[016789][-. ]?[0-9]{3,4}[-. ]?[0-9]{4}\b|\+[0-9]{1,3}[- ][0-9][- 0-9]{7,16}[0-9]\b"),
        ("personal_data", "national_id", r"\b[0-9]{6}-[0-9]{7}\b|\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b"),
        ("personal_data", "account_number", r"\b[A-Z]{2}[0-9]{2}(?: ?[A-Z0-9]){11,30}\b"),
        ("injection", "prompt_override", r"(?i)ignore (?:all )?previous instructions|disregard previous instructions|이전 지시(?:사항)?(?:를|을)? 무시|send the document to\s+http|외부로 전송|run the following command|비밀번호를 입력"),
    ].into_iter().map(|(reason, code, pattern)| (reason, code, Regex::new(pattern).expect("static review pattern"))).collect())
}
pub fn contains_secret(text: &str) -> bool {
    let text = normalized(text);
    patterns()
        .iter()
        .any(|(reason, _, pattern)| *reason == "secret" && pattern.is_match(&text))
        || assignment()
            .captures_iter(&text)
            .any(|captures| credential_value_is_secret(&captures[1]))
}
pub fn contains_injection(text: &str) -> bool {
    let text = normalized(text);
    patterns()
        .iter()
        .any(|(reason, _, pattern)| *reason == "injection" && pattern.is_match(&text))
}
fn assignment() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new(r"(?i)\b(?:password|passwd|secret|api_key|apikey|access_token|auth_token)\s*[:=]\s*(\S{8,})").unwrap())
}
fn credential_value_is_secret(value: &str) -> bool {
    !["{{", "<", "$"].iter().any(|p| value.starts_with(p))
        && !value.chars().all(|c| "_*.-xX#".contains(c))
}
fn cards() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new(r"\b[0-9](?:[ -]?[0-9]){12,18}\b").unwrap())
}
fn markup() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new(r"(?i)</?[a-z]|javascript:| on[a-z]+=").unwrap())
}
fn luhn(value: &str) -> bool {
    let digits: Vec<u32> = value.chars().filter_map(|c| c.to_digit(10)).collect();
    if !(13..=19).contains(&digits.len()) {
        return false;
    }
    digits
        .iter()
        .rev()
        .enumerate()
        .map(|(i, d)| {
            let n = if i % 2 == 1 { d * 2 } else { *d };
            if n > 9 { n - 9 } else { n }
        })
        .sum::<u32>()
        % 10
        == 0
}
fn add(
    findings: &mut BTreeSet<ReviewFinding>,
    rule: &str,
    field: &str,
    code: &str,
    reason: &str,
    action: &str,
) {
    findings.insert(ReviewFinding {
        rule: rule.into(),
        field: field.into(),
        code: code.into(),
        reason: reason.into(),
        action: action.into(),
    });
}
/// Findings contain fixed codes and field paths only, never matched values or offsets.
/// Duplicate structures are human-review advisories: licensed derivative contributions may coexist.
pub fn review_snapshot(contribution_id: &str, t: &Template, catalog: &[Template]) -> ReviewReport {
    let mut findings = BTreeSet::new();
    if t.visibility != Visibility::Public || !t.id.starts_with("public_") || t.version == 0 {
        add(
            &mut findings,
            "R0",
            "snapshot",
            "invalid_snapshot",
            "structure",
            "block",
        );
    }
    let mut fields = vec![
        ("title".to_string(), t.title.as_str(), 120),
        ("summary".into(), t.summary.as_str(), 600),
        ("author".into(), t.author.as_str(), 80),
    ];
    fields.extend(
        t.sections
            .iter()
            .enumerate()
            .map(|(i, s)| (format!("sections[{i}]"), s.as_str(), 60)),
    );
    fields.extend(
        t.tags
            .iter()
            .enumerate()
            .map(|(i, s)| (format!("tags[{i}]"), s.as_str(), 32)),
    );
    if let Some(origin) = &t.origin {
        fields.push(("origin.author".into(), origin.author.as_str(), 80));
    }
    fields.extend(
        t.attributions
            .iter()
            .enumerate()
            .map(|(i, o)| (format!("attributions[{i}].author"), o.author.as_str(), 80)),
    );
    if let Some(variant) = &t.form.variant {
        fields.push(("form.variant".into(), variant.as_str(), 80));
    }
    for (field, raw, limit) in fields {
        let text = normalized(raw);
        let compact = text.split_whitespace().collect::<Vec<_>>().join(" ");
        for (reason, code, re) in patterns() {
            if re.is_match(&compact) {
                add(&mut findings, "R1", &field, code, reason, "block");
            }
        }
        for captures in assignment().captures_iter(&text) {
            let value = &captures[1];
            if credential_value_is_secret(value) {
                add(
                    &mut findings,
                    "R1",
                    &field,
                    "credential_assignment",
                    "secret",
                    "block",
                );
            }
        }
        if cards().find_iter(&text).any(|m| luhn(m.as_str())) {
            add(
                &mut findings,
                "R1",
                &field,
                "card_number",
                "personal_data",
                "block",
            );
        }
        if raw.chars().count() > limit {
            add(
                &mut findings,
                "R4",
                &field,
                "limit_exceeded",
                "structure",
                "block",
            );
        }
        if (field == "title" || field == "author" || field.starts_with("sections["))
            && text.trim().is_empty()
        {
            add(
                &mut findings,
                "R4",
                &field,
                "empty_field",
                "structure",
                "block",
            );
        }
        if raw
            .chars()
            .any(|c| c.is_control() && !(field == "summary" && ['\n', '\r', '\t'].contains(&c)))
        {
            add(
                &mut findings,
                "R4",
                &field,
                "control_char",
                "structure",
                "block",
            );
        }
        if markup().is_match(&text) {
            add(&mut findings, "R4", &field, "markup", "structure", "block");
        }
    }
    let permitted = |license: &str| ["CC0-1.0", "CC-BY-4.0"].contains(&license);
    if !permitted(&t.license) {
        add(
            &mut findings,
            "R2",
            "license",
            "license_not_allowed",
            "license",
            "block",
        );
    }
    for o in t.origin.iter().chain(t.attributions.iter()) {
        if !permitted(&o.license) || (o.license == "CC-BY-4.0" && t.license != "CC-BY-4.0") {
            add(
                &mut findings,
                "R2",
                "license",
                "relicense_forbidden",
                "license",
                "block",
            );
        }
    }
    if t.sections.is_empty()
        || t.sections.len() > 12
        || t.tags.len() > 8
        || t.attributions.len() > 16
    {
        add(
            &mut findings,
            "R4",
            "snapshot",
            "limit_exceeded",
            "structure",
            "block",
        );
    }
    let form = dmem_contracts::FormInput {
        provider: serde_json::from_value::<String>(serde_json::to_value(t.form.provider).unwrap())
            .unwrap(),
        doc_type: t.form.doc_type.clone(),
        locale: t.form.locale.clone(),
        region: t.form.region.clone(),
        variant: t.form.variant.clone(),
        page: t.form.page.clone(),
    };
    if !crate::normalize_form(form).is_ok_and(|f| f == t.form) {
        add(
            &mut findings,
            "R4",
            "form",
            "invalid_form",
            "structure",
            "block",
        );
    }
    let key = structure_key(t);
    let sections: BTreeSet<_> = t.sections.iter().map(|s| canonical(s)).collect();
    for candidate in catalog.iter().filter(|c| c.id != t.id) {
        if structure_key(candidate) == key {
            add(
                &mut findings,
                "R3",
                &format!("public:{}", candidate.id),
                "exact_duplicate",
                "duplicate",
                "review",
            );
        } else if candidate.form.doc_type == t.form.doc_type
            && candidate.form.locale == t.form.locale
        {
            let other: BTreeSet<_> = candidate.sections.iter().map(|s| canonical(s)).collect();
            let union = sections.union(&other).count();
            if union > 0 && sections.intersection(&other).count() * 5 >= union * 4 {
                add(
                    &mut findings,
                    "R3",
                    &format!("public:{}", candidate.id),
                    "near_duplicate",
                    "duplicate",
                    "review",
                );
            }
        }
    }
    let findings: Vec<_> = findings.into_iter().collect();
    let blocked = findings.iter().any(|f| f.action == "block");
    let verdict = if blocked {
        "blocked"
    } else if findings.iter().any(|f| f.action == "review") {
        "needs_review"
    } else {
        "ready"
    };
    let reasons = findings
        .iter()
        .filter(|f| !blocked || f.action == "block")
        .map(|f| f.reason.clone())
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect();
    let stages = [
        ("R0", "Submission and snapshot"),
        ("R1", "Privacy and injection"),
        ("R2", "License and attribution"),
        ("R3", "Duplicate structures"),
        ("R4", "Structure validation"),
        ("R5", "Administrator decision"),
    ]
    .into_iter()
    .map(|(rule, label)| {
        let status = if rule == "R5" {
            "pending"
        } else if findings
            .iter()
            .any(|f| f.rule == rule && f.action == "block")
        {
            "blocked"
        } else if findings
            .iter()
            .any(|f| f.rule == rule && f.action == "review")
        {
            "needs_review"
        } else {
            "passed"
        };
        ReviewStage {
            rule: rule.into(),
            label: label.into(),
            status: status.into(),
        }
    })
    .collect();
    ReviewReport {
        schema_version: 1,
        policy: "contribution-review-v1".into(),
        contribution_id: contribution_id.into(),
        snapshot_version: t.version,
        snapshot_hash: format!(
            "sha256:{:x}",
            Sha256::digest(serde_json::to_vec(t).expect("serializable template"))
        ),
        verdict: verdict.into(),
        reasons,
        findings,
        stages,
        decision: None,
        decided_at: None,
    }
}
