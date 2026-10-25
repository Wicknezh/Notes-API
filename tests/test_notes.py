NOTE = {"title": "Hello", "content": "World"}


def create_note(client, headers, **overrides) -> dict:
    r = client.post("/notes", json={**NOTE, **overrides}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()




def test_list_notes_without_token_401(client):
    assert client.get("/notes").status_code == 401


def test_create_note_without_token_401(client):
    assert client.post("/notes", json=NOTE).status_code == 401




def test_viewer_can_read(client, alice, viewer):
    note = create_note(client, alice)
    assert client.get("/notes", headers=viewer).status_code == 200
    assert client.get(f"/notes/{note['id']}", headers=viewer).status_code == 200


def test_viewer_cannot_create_403(client, viewer):
    assert client.post("/notes", json=NOTE, headers=viewer).status_code == 403


def test_viewer_cannot_edit_403(client, alice, viewer):
    note = create_note(client, alice)
    r = client.put(f"/notes/{note['id']}", json={"title": "Hacked"}, headers=viewer)
    assert r.status_code == 403


def test_viewer_cannot_delete_403(client, alice, viewer):
    note = create_note(client, alice)
    assert client.delete(f"/notes/{note['id']}", headers=viewer).status_code == 403



def test_user_can_create_and_owns_note(client, alice):
    note = create_note(client, alice)
    me = client.get("/auth/me", headers=alice).json()
    assert note["owner_id"] == me["id"]


def test_user_can_edit_own_note(client, alice):
    note = create_note(client, alice)
    r = client.put(f"/notes/{note['id']}", json={"title": "Updated"}, headers=alice)
    assert r.status_code == 200
    assert r.json()["title"] == "Updated"
    assert r.json()["content"] == "World"  # untouched field is kept


def test_user_can_delete_own_note(client, alice):
    note = create_note(client, alice)
    assert client.delete(f"/notes/{note['id']}", headers=alice).status_code == 204
    assert client.get(f"/notes/{note['id']}", headers=alice).status_code == 404


def test_user_cannot_edit_others_note_403(client, alice, bob):
    note = create_note(client, alice)
    r = client.put(f"/notes/{note['id']}", json={"title": "Mine now"}, headers=bob)
    assert r.status_code == 403
    # and the note is unchanged
    assert client.get(f"/notes/{note['id']}", headers=alice).json()["title"] == "Hello"


def test_user_cannot_delete_others_note_403(client, alice, bob):
    note = create_note(client, alice)
    assert client.delete(f"/notes/{note['id']}", headers=bob).status_code == 403
    assert client.get(f"/notes/{note['id']}", headers=alice).status_code == 200




def test_admin_can_edit_any_note(client, alice, admin):
    note = create_note(client, alice)
    r = client.put(f"/notes/{note['id']}", json={"content": "Edited by admin"}, headers=admin)
    assert r.status_code == 200
    assert r.json()["content"] == "Edited by admin"


def test_admin_can_delete_any_note(client, alice, admin):
    note = create_note(client, alice)
    assert client.delete(f"/notes/{note['id']}", headers=admin).status_code == 204
    assert client.get(f"/notes/{note['id']}", headers=admin).status_code == 404




def test_get_missing_note_404(client, alice):
    assert client.get("/notes/999", headers=alice).status_code == 404


def test_update_missing_note_404(client, alice):
    assert client.put("/notes/999", json={"title": "x"}, headers=alice).status_code == 404


def test_delete_missing_note_404(client, alice):
    assert client.delete("/notes/999", headers=alice).status_code == 404


def test_viewer_gets_403_not_404_on_missing_note(client, viewer):
    assert client.delete("/notes/999", headers=viewer).status_code == 403


def test_create_note_empty_title_422(client, alice):
    assert client.post("/notes", json={"title": "", "content": "x"}, headers=alice).status_code == 422


def test_update_with_null_title_is_ignored(client, alice):
    note = create_note(client, alice)
    r = client.put(f"/notes/{note['id']}", json={"title": None}, headers=alice)
    assert r.status_code == 200
    assert r.json()["title"] == "Hello"