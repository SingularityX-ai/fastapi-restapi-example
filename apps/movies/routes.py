from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..database import get_db
from . import schemas, models

from apps.directors.models import Director as DirectorModel


router = APIRouter(
    tags = ["Movies"]
)


@router.get('/movies', response_model=List[schemas.Movie])
def get_movies( title: str=None,
                rating: float=None,
                min_year: int=None,
                max_year: int=None,
                db: Session = Depends(get_db)):
"""
Retrieve movies based on the provided filters.

Args:
- title (str, optional): Title of the movie to filter by.
- rating (float, optional): Rating of the movie to filter by.
- min_year (int, optional): Minimum release year of the movie to filter by.
- max_year (int, optional): Maximum release year of the movie to filter by.
- db (Session): Database session dependency.

Returns:
- List[models.Movie]: List of movies matching the provided filters.

Raises:
- No specific exceptions are raised within this function.

Example:
movies = get_movies(title="The Matrix", min_year=1999, db=session)
"""

    query = db.query(models.Movie)
                    
    if title:
        query = query.filter(models.Movie.title.ilike(f"%{title}%"))
    if rating is not None:
        query = query.filter(or_(models.Movie.rating==rating, models.Movie.rating.like(f"{rating}")))
    if min_year:
        query = query.filter(models.Movie.year >= min_year)
    if max_year:
        query = query.filter(models.Movie.year <= max_year)
    movies = query.all()
    return movies


@router.get('/movies/{movie_id}', response_model=schemas.Movie)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a movie by its ID from the database.

    Args:
        movie_id (int): The ID of the movie to retrieve.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Raises:
        HTTPException: If the movie with the specified ID is not found in the database.

    Returns:
        models.Movie: The movie retrieved from the database.

    Example:
        movie = get_movie(123)
    """

    db_movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
        
    return db_movie


@router.post('/movies', response_model=schemas.Movie)
def create_movie(movie: schemas.MovieCreate, db: Session = Depends(get_db)):
    if not db.query(DirectorModel).filter(DirectorModel.id == movie.director_id).first():
        raise HTTPException(status_code=400, detail="Invalid director_id")
    db_movie = models.Movie(
        title=movie.title,
        year=movie.year,
        rating=movie.rating,
        runtime=movie.runtime,
        genre=movie.genre,
        director_id=movie.director_id
    )
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie


@router.put('/movies/{movie_id}', response_model=schemas.Movie)
def update_movie(movie_id: int, movie_update: schemas.MovieCreate, db: Session = Depends(get_db)):
    db_movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    if not movie_id:
        raise HTTPException(status_code=404, detail="Movie not found")
    for field, value in movie_update.dict(exclude_unset=True).items():
        setattr(db_movie, field, value)
    db.commit()
    db.refresh(db_movie)
    return db_movie


@router.delete('/movies/{movie_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    """
    Delete a movie from the database.

    Args:
        movie_id (int): The ID of the movie to be deleted.
        db (Session): The database session.

    Raises:
        HTTPException: If the movie with the given ID is not found in the database.

    Returns:
        None: Returns None after deleting the movie.

    Example:
        delete_movie(123, db)
    """

    db_movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    db.delete(db_movie)
    db.commit()
    return None
