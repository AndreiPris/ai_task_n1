import chromadb
import json
from sentence_transformers import SentenceTransformer
import os

def create_persistent_database():
    db_path = "./chroma_db" # место где я храню базу данных чтобы не создавать временную база данных
    
    client = chromadb.PersistentClient(path=db_path) # создал клиента и сохранил в папку
    #model = SentenceTransformer('all-MiniLM-L6-v2') # загружаю моедель которая преобразует текст в embeding (она стоит по умолчанию)
    
    f = open('data.json', 'r', encoding='utf-8')# читаем('r') файл c данными, encoding для работы я языками
    data = json.load(f) # присваемаем файл в переменную data
    f.close() # обязателбно закрываем файл иначе ошибка
    
    products = data['products'] # записваем в переменную массив из 
    
    categories = {} 
    for product in products: # создаем категории 
        category = product['category']
        if category not in categories:
            categories[category] = []
        categories[category].append(product)
    
    for category_name, category_products in categories.items():
        collection_name = f"darwin_{category_name}"
        
        try: # при повторном завпске удалает предидущую коллекцию
            client.delete_collection(collection_name)
        except:
            pass
        
        collection = client.create_collection(name=collection_name)
        
        ids = []
        documents = []
        metadatas = []
        
        for product in category_products:
            ids.append(str(product['id'])) 
            documents.append(f"{product['name']} {product['description']}")
            
            metadata = {
                'name': product['name'],
                'description': product['description'],
                'price': product['price'],
                'category': product['category']
            }
            metadatas.append(metadata)
        
        #embeddings = model.encode(documents).tolist() #преобразуем в векторы 
        
        collection.add(
            ids=ids,
            documents=documents,
            #embeddings=embeddings,
            metadatas=metadatas
        )
    # test
    test_collection = client.get_collection("darwin_smartphones")
    results = test_collection.query(
        query_texts=["iPhone Apple"],
        n_results=3
    )
    
    return client

if __name__ == "__main__":
    create_persistent_database()