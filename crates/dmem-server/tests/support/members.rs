use dmem_server::Store;
use rusqlite::{Connection, params};
use std::{path::Path, sync::Arc};

// Bearer fixtures represent registered members; bare local owners cannot contribute.
pub fn open_member_store(path: &Path, owners: &[&str]) -> Arc<Store> {
    let store = Arc::new(Store::open(path).unwrap());
    let db = Connection::open(path).unwrap();
    for owner in owners {
        db.execute(
            "INSERT OR IGNORE INTO accounts(id,email,created_at) VALUES(?1,?2,1)",
            params![owner, format!("{owner}@example.test")],
        )
        .unwrap();
    }
    store
}
