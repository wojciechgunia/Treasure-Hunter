import typer
from app import database, models
from app.services.authService import get_password_hash

app = typer.Typer()


@app.command()
def create_user(login: str, password: str, role: str = "user"):
    db = database.SessionLocal()
    user = models.User(
        login=login,
        password=get_password_hash(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"Utworzono użytkownika: {user.login} (id={user.id})")


if __name__ == "__main__":
    app()
