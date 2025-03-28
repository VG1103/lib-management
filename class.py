from abc import ABC,abstractmethod
from fastapi import FastAPI,HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import string,random

app = FastAPI()

mongo_url = "mongodb://localhost:27017/"
client = AsyncIOMotorClient(mongo_url)
db = client.lib_db
book_collection = db.books
ebook_collection = db.ebooks
Key_collection = db.api_keys


class BaseBook(ABC) :
  
  @abstractmethod
  def addBook(self,title):
    new_book = {
      "Title":title
    }
    result =  book_collection.insert_one(new_book)
    return {"message":"book successfully added","id": str(result.inserted_id)}


  @abstractmethod
  def getBook(self,id):
    pass
  #   try:
  #     book_object_id = ObjectId(book_id)
  #   except ValueError as e:
  #     raise HTTPException(status_code=400 , detail= str(e))
  #   book = book_collection.find_one({"_id":book_object_id})
  #   if not book:
  #     raise HTTPException(status_code= 404, detail= "cannot find resource")
  #   book["_id"] = str(book["_id"])
  #   return book

  @abstractmethod
  def getAllBooks(self):
    pass
  
  @abstractmethod
  def removeBooks(self,id):
    pass

 
class Book(BaseBook):
  def __init__(self,title,author,genre):
    self.title = title
    self.author = author
    self.genre = genre
    self.is_issued = False
    self.issued_to = None
  
  async def addBook(self, title, author, genre):
    new_book = {
      "Title": title,
      "Author": author,
      "Genre":genre
    }
    try:
      result = await book_collection.insert_one(new_book)
      return {"message": "Book added successfully", "id": str(result.inserted_id)}
    except Exception as e:
      raise HTTPException(status_code=500, detail= f"Database Error: {str(e)}")
  
  async def getBook(self,book_id ):
    try:
        book_object_id = ObjectId(book_id)  
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")
    book = await book_collection.find_one({"_id":book_object_id})
    if not book:
        raise HTTPException(status_code=404,detail = "Book not found")
    book["_id"] = str(book["_id"])
    return book
  
  async def getAllBooks(self):
    try:
      books = await book_collection.find().to_list(100)
      for book in books:
        book["_id"] = str(book["_id"])
      return books 
    except Exception as e:
      raise HTTPException(status_code= 500, detail=f"database error: {str(e)}")
    
  async def issueBook(self, book_id, issued_to):
    book_object_id = ObjectId(book_id)
    book = await book_collection.find_one({"_id":book_object_id})
    if not book:
      raise HTTPException(status_code=404,detail="Book not found")
    if book["is_issued"]:
      raise HTTPException(status_code=400, detail="Book is already issued")
    result = await book_collection.update_one({"_id": book_object_id},{"$set":{"is_issued":True,"issued_to": issued_to}})
    if result.modified_count == 1:
      return {"message":"Book issued sucseefully","book_id":book_id,"issued_to":issued_to}
    else:
      raise HTTPException(status_code=500,detail="Error issuing book")
  
  async def returnBook(self,book_id):
    try:
      book_object_id = ObjectId(book_id)
      book = await book_collection.find_one({"_id": book_object_id})
      if not book:
        raise HTTPException(status_code=404,detail="Book not found")
      result = await book_collection.update_one(({"_id":book_object_id}),{"$set":{"is_issued":False,"issued_to": None}})
      if result.modified_count == 1:
        return{"message":"Book returned successfully","book_id" : book_id}
      else:
        raise HTTPException(status_code=500, detail="Error returning book")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error returning book: {str(e)}")
    
  async def removeBook(self,book_id):
    try:
      book_object_id = ObjectId(book_id)
      book = await book_collection.delete_one({"_id":book_object_id})
      if book.deleted_count == 1:
        return {"message":"book deleted sucessfully","_id":book_id}
      else:
        raise HTTPException(status_code=404, detail="Book not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting book: {str(e)}")
  

class Ebook(BaseBook):
  def __init__(self,title,author,genre,link):
    self.title = title
    self.author = author
    self.genre = genre
    self.link = link
  
  async def addEbook(self,title,author,genre,link):
    new_book = {
      "Title": title,
      "Author": author,
      "Genre": genre,
      "link":link
    }
    result = await ebook_collection.insert_one(new_book)
    return {"message":"Added successfully","id":str(result.inserted_id)}
  
  async def getEbook(self,ebook_id):
    ebook_object_id = ObjectId(ebook_id)
    ebook = await ebook_collection.find_one({"_id":ebook_object_id})
    ebook["-id"] = str(ebook["_id"])
    return ebook
    
  async def gettAllEbooks(self):
    ebooks = await ebook_collection.find().to_list(100)
    for ebook in ebooks:
      ebook["_id"] = str(ebook["_id"])
    return ebooks
  
  async def removeEbooks(self,ebook_id):
    ebook_object_id = ObjectId(ebook_id)
    ebook = await ebook_collection.delete_one({"_id":ebook_object_id})
    ebook["_id"] = str(ebook["_id"])
    return {"message":"ebook deleted successfully"}



@app.post("/addBooks/")
async def addBooks(title : str,author: str, genre :str):
  book = Book(title,author,genre)
  result = await book.addBook(title,author,genre)
  return result

@app.get("/getBooks/{book_id}")
async def getBooks(book_id:str):
  book = Book("","","")
  book_data = await book.getBook(book_id)
  return book_data
  
@app.post("/allBooks/")
async def allBooks():
  book = Book("","","")
  books = await book.getAllBooks()
  return books
  
@app.post("/issueBook/{book_id}")
async def issueBook(book_id: str,issued_to:str):
  book = Book("","","")
  result = await book.issueBook(book_id,issued_to)
  return result

@app.post("/returnBook/{book_id}")
async def returnBook(book_id:str):
  book = Book("","","")
  result = await book.returnBook(book_id)
  return result

@app.delete("/deleteBook")
async def deleteBook(book_id :str, title:str,author:str,genre:str):
  book = Book(title,author,genre)
  deleted_book = await book.removeBook(book_id)
  return {"message":"deleted sucessfully","deleted_book_id":book_id}

  

@app.post("/addEbooks/")
async def addEbook(title: str,author:str,genre:str,link:str):
  ebook = Ebook(title,author,genre,link)
  result = await ebook.addEbook(title,author,genre,link)
  return result

@app.get("/getEbook/{ebook_id}")
async def getEbook(ebook_id :str):
  ebook = Ebook("","","","")
  ebook_data = await ebook_collection.getEbook(ebook_id) 
  return ebook_data

@app.post("/getAllEbooks")
async def getAllEbooks():
  ebook = Ebook("","","","")
  ebooks = await ebook.getAllBooks()
  return ebooks

@app.delete("/deleteEbook")
async def deleteEbooks(ebook_id:str,title:str,author:str,genre:str,link:str):
  ebook = Ebook(title,author,genre,link)
  deleted_ebook = await ebook.removeEbooks(ebook_id)
  return {"message":"deleted succsessfully","deleted_ebook_id":ebook_id}

@app.get("/authenticate")
async def authApi(key):
  key_check = await Key_collection.find_one({"api_key" : key})
  if key_check:
    return {"message": "Authentication Sucessful"}
  else:
    raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key")


#API KEYS
#generate api key

def generate_key(length=32):
  characters = string.ascii_letters + string.digits
  key = ''.join(random.choices(characters,k=length))
  return key

#store key
async def store_key(key):
  await Key_collection.insert_one({"api_key": key,"active":True})
  return key

#api caal
@app.get("/generateKey")
async def generateKey():
  key = generate_key()
  stored_key = await store_key(key)
  return {"api_key": stored_key}