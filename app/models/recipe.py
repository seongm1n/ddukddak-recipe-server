from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class Recipe(Base, TimestampMixin):
    __tablename__ = "recipes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    video_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    video_url: Mapped[str] = mapped_column(String(500))
    title: Mapped[str] = mapped_column(String(500))
    thumbnail_url: Mapped[str] = mapped_column(String(500))
    channel_name: Mapped[str] = mapped_column(String(200))
    steps: Mapped[list] = mapped_column(JSON)
    total_cost: Mapped[int] = mapped_column(Integer)
    servings: Mapped[int] = mapped_column(Integer)

    ingredients: Mapped[list["Ingredient"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    recipe_id: Mapped[str] = mapped_column(String(36), ForeignKey("recipes.id"))
    name: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[str] = mapped_column(String(50))
    unit: Mapped[str] = mapped_column(String(20))
    price: Mapped[int] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(String(500), default=None)
    display_order: Mapped[int] = mapped_column(Integer)

    recipe: Mapped["Recipe"] = relationship(back_populates="ingredients")


class UserSavedRecipe(Base, TimestampMixin):
    __tablename__ = "user_saved_recipes"
    __table_args__ = (
        UniqueConstraint("user_id", "recipe_id", name="uq_user_recipe"),
        Index("idx_user_saved_recipe_user_id", "user_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    recipe_id: Mapped[str] = mapped_column(String(36), ForeignKey("recipes.id"))
