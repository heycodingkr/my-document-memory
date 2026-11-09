use dmem_mcp::bridge::validate_target;
use serde_json::json;
fn context() -> serde_json::Value {
    json!({"ok":true,"session_id":"owned","automation_target_tab":7,"tabs":[{"tab_id":7,"window_id":3,"is_automation_target":true,"is_mine":true,"ready":true,"url":"https://example.com/document?private=1","owner":{"session_id":"owned","client_name":"dmem-browser-mcp","is_mine":true,"tab_id":7,"window_id":3,"expires_at_ms":9999999999999_u64}}]})
}
#[test]
fn wi20_owned_ready_target_is_accepted() {
    assert!(validate_target(&context(), "owned").is_ok());
}
#[test]
fn wi21_foreign_expired_unready_or_missing_private_lease_is_rejected() {
    let mut cases = vec![];
    let mut v = context();
    v["tabs"][0]["is_mine"] = json!(false);
    cases.push(v);
    let mut v = context();
    v["tabs"][0]["owner"]["session_id"] = json!("other");
    cases.push(v);
    let mut v = context();
    v["tabs"][0]["owner"]["client_name"] = json!("other");
    cases.push(v);
    let mut v = context();
    v["tabs"][0]["owner"]["expires_at_ms"] = json!(1);
    cases.push(v);
    let mut v = context();
    v["tabs"][0]["ready"] = json!(false);
    cases.push(v);
    let mut v = context();
    v["tabs"][0]["has_local_lease"] = json!(false);
    cases.push(v);
    let mut v = context();
    v["tabs"][0]["owner"]["window_id"] = json!(4);
    cases.push(v);
    let mut v = context();
    v["automation_target_tab"] = json!(8);
    cases.push(v);
    for v in cases {
        assert!(validate_target(&v, "owned").is_err(), "{v}");
    }
    assert!(validate_target(&context(), "other").is_err());
}
