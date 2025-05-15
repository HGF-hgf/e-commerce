# e-commerce

# Structure
```bash
📁 Project Root
├── .gitignore
├── README.md
├── chatbot.py                file chứa hàm để chatbot xử lý query và response
├── chatbot.txt            
├── config.py                 file khai báo database và các api key
├── core.py                   file chứa logic reflection để phục vụ lưu lịch sử chat
├── embedd_data.py
├── embeddings.json
├── embeddings.py             file hàm embedding phục vụ embedding query và data
├── fastapi_test.py           file tạo api để giao tiếp giữa frontend và backend
├── requirements.txt          file chứa các thư viện cần cài đặt để chạy chương trình
├── sample_query.py           chứa một số câu query để phục vụ semantic router
├── semantic_router.py        sử dụng để phục vụ mục đích giúp chatbot phân biệt được giữa chitchat query và product query
├── tools.py                  file chứa thông tin khai báo các tools để lấy thông tin từ database
└── vector_query_engine.py    file khai báo các query engine để chatbot thực hiện truy xuất thông tin khi nhận được query
```

# Công nghệ sử dụng

* OpenAI model: gpt-4o
* Google embedding model: gemini-embedding-exp-03-07
* LLama agent for agentic RAG
* fastapi
* MongoDB and Mongo Atlas for public database

# Installation

* Cài đặt các thư viện cần thiết
```bash
pip inntall -r requirements.txt
```

* tạo file .env và thêm api key và database connection string
```bash
OPENAI_API_KEY = ...
MONGODB_URl = ...
GOOGLE_API_KEY = ...
```

* chạy file chứa fastapi để chatbot hoạt động
```bash
uvicorn fastapi_test:app --reload
```
