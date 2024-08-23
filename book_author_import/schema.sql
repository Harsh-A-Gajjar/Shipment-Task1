DROP TABLE IF EXISTS books CASCADE;
DROP TABLE IF EXISTS authors CASCADE;

CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    date_of_birth DATE NOT NULL
);

CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    isbn_code TEXT NOT NULL,
    author_id INTEGER REFERENCES authors(id)
);
