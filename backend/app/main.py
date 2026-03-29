from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, admin, employee, manager, ocr

app = FastAPI(title="Reimbursement Management System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(employee.router)
app.include_router(manager.router)
app.include_router(ocr.router)

@app.get("/")
def read_root():
    return {"message": "Reimbursement Management System API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
