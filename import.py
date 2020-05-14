from sqlalchemy import create_engine
import csv
from sqlalchemy.orm import scoped_session, sessionmaker

def main():
    engine = create_engine("postgres://vfrqdxwcyogetg:96cccefe8951dcc704c73fd70bc30b1e3b63348c118668de0bdf9fec3e259106@ec2-54-157-78-113.compute-1.amazonaws.com:5432/d6vbal80o42meg")
    books = scoped_session(sessionmaker(bind=engine))

    books.execute("DROP TABLE IF EXISTS books")
    books.execute("CREATE TABLE books(ISBN VARCHAR PRIMARY KEY, TITLE VARCHAR NOT NULL, AUTHOR VARCHAR NOT NULL, YEAR VARCHAR NOT NULL);")

    with open("books.csv") as f:
        reader = csv.reader(f)
        for ISBN, TITLE, AUTHOR, YEAR in reader:
            books.execute("INSERT INTO books(ISBN, TITLE, AUTHOR, YEAR) VALUES (:ISBN, :TITLE, :AUTHOR, :YEAR)",
            {"ISBN":ISBN, "TITLE":TITLE, "AUTHOR":AUTHOR, "YEAR":YEAR})
            books.commit()

if __name__ == "__main__"
    main()