SECOND_USER = {
    "email": "jamie@example.com",
    "username": "jamie_lee",
    "password": "second-user-1",
}


def test_registered_pet_belongs_to_new_user(client, register_payload):
    resp = client.post("/api/auth/register", json=register_payload)
    pet_id = resp.json()["pet"]["id"]

    my_pets = client.get("/api/pets").json()
    assert len(my_pets) == 1
    assert my_pets[0]["id"] == pet_id
    assert my_pets[0]["name"] == "Bruno"


def test_list_pets_requires_authentication(client):
    resp = client.get("/api/pets")
    assert resp.status_code == 401


def test_create_pet_requires_authentication(client):
    resp = client.post("/api/pets", json={"name": "Rex"})
    assert resp.status_code == 401


def test_create_pet_attaches_to_current_user(client, register_payload):
    client.post("/api/auth/register", json=register_payload)

    resp = client.post("/api/pets", json={"name": "Rex", "breed": "Beagle"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "Rex"

    my_pets = client.get("/api/pets").json()
    names = {p["name"] for p in my_pets}
    assert names == {"Bruno", "Rex"}


def test_user_cannot_read_another_users_pet(client, register_payload):
    # User A registers with Bruno.
    resp_a = client.post("/api/auth/register", json=register_payload)
    bruno_id = resp_a.json()["pet"]["id"]

    # Log out user A, register user B.
    client.post("/api/auth/logout")
    client.post("/api/auth/register", json=SECOND_USER)

    # User B tries to fetch user A's pet by ID.
    resp = client.get(f"/api/pets/{bruno_id}")
    assert resp.status_code == 404


def test_user_cannot_update_another_users_pet(client, register_payload):
    resp_a = client.post("/api/auth/register", json=register_payload)
    bruno_id = resp_a.json()["pet"]["id"]

    client.post("/api/auth/logout")
    client.post("/api/auth/register", json=SECOND_USER)

    resp = client.patch(f"/api/pets/{bruno_id}", json={"name": "Hijacked"})
    assert resp.status_code == 404


def test_nonexistent_pet_id_returns_404(client, register_payload):
    client.post("/api/auth/register", json=register_payload)
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = client.get(f"/api/pets/{fake_id}")
    assert resp.status_code == 404
