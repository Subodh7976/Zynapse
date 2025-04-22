from sqlalchemy.exc import IntegrityError
import pytest
import uuid
import os


from app.core.models import (
    Base, Conversation, Source, SourceTypeEnum,
    DATABASE_URL, engine as app_engine, SessionLocal as AppSessionLocal
)

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", DATABASE_URL)
if TEST_DATABASE_URL == DATABASE_URL:
    print("\n⚠️ WARNING: Running tests against the main DATABASE_URL."
          " Ensure this is a test database or data might be affected. ⚠️\n")


test_engine = app_engine
TestSessionLocal = AppSessionLocal


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Creates tables once before any tests run."""
    print("\nSetting up test database schema...")
    # Drop existing tables first for a clean slate (optional, use with caution)
    # Base.metadata.drop_all(bind=test_engine)
    try:
        Base.metadata.create_all(bind=test_engine)
        print("Test database schema created.")
    except Exception as e:
        print(f"\n🚨 Error creating test schema: {e}. Ensure database is running and accessible.")
        pytest.fail(f"Database setup failed: {e}")
    yield
    # Optional: Clean up after all tests are done
    # print("\nTearing down test database schema...")
    # Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def db_session(setup_database):
    """Provides a transactional scope for tests."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    print("\n[DB Test] Transaction started.")
    yield session # Provide the session to the test

    print("[DB Test] Rolling back transaction.")
    session.close()
    transaction.rollback() # Rollback changes after each test
    connection.close()

# --- Test Cases ---

def test_create_conversation(db_session):
    """Test creating a simple Conversation object."""
    title = f"Test Conversation {uuid.uuid4()}"
    conv = Conversation(
        title=title,
        conversation_data={"history": [], "metadata": {"user": "test_user"}}
    )
    db_session.add(conv)
    db_session.commit() # Commit to assign ID, created_at etc.

    assert conv.id is not None
    assert isinstance(conv.id, uuid.UUID)
    assert conv.title == title
    assert conv.created_at is not None
    assert conv.updated_at is not None
    assert conv.conversation_data == {"history": [], "metadata": {"user": "test_user"}}
    assert conv.sources == [] # Should be empty initially

    # Verify timestamps are timezone-aware (if timezone=True is effective)
    assert conv.created_at.tzinfo is not None

    # Query back from DB
    retrieved_conv = db_session.query(Conversation).filter(Conversation.id == conv.id).one()
    assert retrieved_conv is not None
    assert retrieved_conv.id == conv.id
    assert retrieved_conv.title == title
    assert retrieved_conv.conversation_data == conv.conversation_data

def test_update_conversation(db_session):
    """Test updating conversation fields."""
    initial_title = "Initial Title"
    conv = Conversation(title=initial_title, conversation_data={"step": 1})
    db_session.add(conv)
    db_session.commit()
    
    conv = db_session.query(Conversation).filter_by(id=conv.id).first()

    conv_id = conv.id
    original_updated_at = conv.updated_at

    # Allow some time to pass for timestamp comparison
    import time
    time.sleep(2)

    # Update fields
    new_title = "Updated Title"
    new_data = {"step": 2, "status": "active"}
    conv.title = new_title
    conv.conversation_data = new_data
    assert db_session.is_modified(conv) # Should be true


    db_session.commit()

    # Query back and check updates
    # updated_conv = db_session.query(Conversation).filter(Conversation.id == conv_id).one()
    db_session.refresh(conv)
    assert conv.title == new_title
    assert conv.conversation_data == new_data
    assert conv.updated_at > original_updated_at



def test_create_source_document(db_session):
    """Test creating a Source of type DOCUMENT."""
    conv = Conversation(title="Doc Test Conversation")
    db_session.add(conv)
    db_session.commit() # Need conversation ID

    source_title = "My Test Document.pdf"
    storage_ref = f"docs/{uuid.uuid4()}.pdf"
    content = "This is the text content of the document."

    source = Source(
        conversation_id=conv.id,
        type=SourceTypeEnum.DOCUMENT,
        storage_reference=storage_ref,
        # link=None, # Should be null for DOCUMENT
        content=content,
        title=source_title,
        path="/papers/2023/"
    )
    db_session.add(source)
    db_session.commit()

    assert source.id is not None
    assert source.conversation_id == conv.id
    assert source.type == SourceTypeEnum.DOCUMENT
    assert source.storage_reference == storage_ref
    assert source.link is None # Check constraint requirement
    assert source.content == content
    assert source.title == source_title
    assert source.path == "/papers/2023/"
    assert source.created_at is not None

    # Query back
    retrieved_source = db_session.query(Source).filter(Source.id == source.id).one()
    assert retrieved_source is not None
    assert retrieved_source.type == SourceTypeEnum.DOCUMENT
    assert retrieved_source.storage_reference == storage_ref
    assert retrieved_source.link is None

def test_create_source_web(db_session):
    """Test creating a Source of type WEB."""
    conv = Conversation(title="Web Test Conversation")
    db_session.add(conv)
    db_session.commit()

    source_title = "SQLAlchemy Website"
    link_url = "https://www.sqlalchemy.org/"
    content = "<html>... SQLAlchemy homepage content ...</html>"

    source = Source(
        conversation_id=conv.id,
        type=SourceTypeEnum.WEB,
        # storage_reference=None, # Should be null for WEB
        link=link_url,
        content=content,
        title=source_title,
    )
    db_session.add(source)
    db_session.commit()

    assert source.id is not None
    assert source.type == SourceTypeEnum.WEB
    assert source.storage_reference is None # Check constraint requirement
    assert source.link == link_url
    assert source.content == content
    assert source.title == source_title
    assert source.path is None # Check default nullable

    # Query back
    retrieved_source = db_session.query(Source).filter(Source.id == source.id).one()
    assert retrieved_source is not None
    assert retrieved_source.type == SourceTypeEnum.WEB
    assert retrieved_source.storage_reference is None
    assert retrieved_source.link == link_url


def test_conversation_source_relationship(db_session):
    """Test the relationship between Conversation and Source."""
    conv = Conversation(title="Relationship Test")
    db_session.add(conv)
    db_session.flush() # Assign conv.id without full commit yet

    source1 = Source(
        conversation_id=conv.id,
        type=SourceTypeEnum.DOCUMENT,
        storage_reference="doc1.txt",
        title="Doc 1"
    )
    source2 = Source(
        conversation_id=conv.id,
        type=SourceTypeEnum.WEB,
        link="http://example.com",
        title="Web 1"
    )

    # Add sources via the relationship
    conv.sources.append(source1)
    conv.sources.append(source2)

    db_session.commit() # Commit conversation and sources

    # --- Verification ---
    conv_id = conv.id
    source1_id = source1.id
    source2_id = source2.id

    # Clear session cache to ensure we query from DB
    db_session.expire_all()

    # Query conversation and check sources (using lazy='selectin')
    retrieved_conv = db_session.query(Conversation).filter(Conversation.id == conv_id).one()
    assert retrieved_conv is not None
    assert len(retrieved_conv.sources) == 2

    # Check source details and back-population
    source_ids = {s.id for s in retrieved_conv.sources}
    assert source_ids == {source1_id, source2_id}

    retrieved_source1 = db_session.query(Source).filter(Source.id == source1_id).one()
    retrieved_source2 = db_session.query(Source).filter(Source.id == source2_id).one()

    assert retrieved_source1.conversation_id == conv_id
    assert retrieved_source2.conversation_id == conv_id
    # Check back_populates
    assert retrieved_source1.conversation is retrieved_conv
    assert retrieved_source2.conversation is retrieved_conv

def test_delete_conversation_cascade(db_session):
    """Test that deleting a Conversation cascades to its Sources."""
    # Create conversation and sources
    conv = Conversation(title="Cascade Delete Test")
    db_session.add(conv)
    db_session.flush()
    source1 = Source(conversation=conv, type=SourceTypeEnum.DOCUMENT, storage_reference="del1.txt", title="Del 1")
    source2 = Source(conversation=conv, type=SourceTypeEnum.WEB, link="http://delete.me", title="Del 2")
    db_session.add_all([source1, source2])
    db_session.commit()

    conv_id = conv.id
    source1_id = source1.id
    source2_id = source2.id

    # Verify creation
    assert db_session.query(Conversation).filter(Conversation.id == conv_id).count() == 1
    assert db_session.query(Source).filter(Source.conversation_id == conv_id).count() == 2

    # Delete the conversation
    db_session.delete(conv)
    db_session.commit()

    # Verify deletion and cascade
    assert db_session.query(Conversation).filter(Conversation.id == conv_id).count() == 0
    assert db_session.query(Source).filter(Source.conversation_id == conv_id).count() == 0 # Sources should be gone
    assert db_session.query(Source).filter(Source.id == source1_id).count() == 0
    assert db_session.query(Source).filter(Source.id == source2_id).count() == 0


def test_source_constraint_violation_document_with_link(db_session):
    """Test check constraint: DOCUMENT type cannot have a link."""
    conv = Conversation(title="Constraint Test Doc")
    db_session.add(conv)
    db_session.commit()

    with pytest.raises(IntegrityError, match=r'check_source_fields_based_on_type'):
        source = Source(
            conversation_id=conv.id,
            type=SourceTypeEnum.DOCUMENT,
            storage_reference="doc.txt",
            link="http://should-not-be-here.com", # Violates constraint
            title="Bad Doc"
        )
        db_session.add(source)
        db_session.commit() # Error occurs on commit

def test_source_constraint_violation_document_missing_ref(db_session):
    """Test check constraint: DOCUMENT type must have storage_reference."""
    conv = Conversation(title="Constraint Test Doc Ref")
    db_session.add(conv)
    db_session.commit()

    with pytest.raises(IntegrityError, match=r'check_source_fields_based_on_type'):
        source = Source(
            conversation_id=conv.id,
            type=SourceTypeEnum.DOCUMENT,
            storage_reference=None, # Violates constraint
            title="Bad Doc Missing Ref"
        )
        db_session.add(source)
        db_session.commit()

def test_source_constraint_violation_web_with_ref(db_session):
    """Test check constraint: WEB type cannot have storage_reference."""
    conv = Conversation(title="Constraint Test Web")
    db_session.add(conv)
    db_session.commit()

    with pytest.raises(IntegrityError, match=r'check_source_fields_based_on_type'):
        source = Source(
            conversation_id=conv.id,
            type=SourceTypeEnum.WEB,
            link="http://valid-link.com",
            storage_reference="ref-should-not-be-here.txt", # Violates constraint
            title="Bad Web"
        )
        db_session.add(source)
        db_session.commit()

def test_source_constraint_violation_web_missing_link(db_session):
    """Test check constraint: WEB type must have link."""
    conv = Conversation(title="Constraint Test Web Link")
    db_session.add(conv)
    db_session.commit()

    with pytest.raises(IntegrityError, match=r'check_source_fields_based_on_type'):
        source = Source(
            conversation_id=conv.id,
            type=SourceTypeEnum.WEB,
            link=None, # Violates constraint
            title="Bad Web Missing Link"
        )
        db_session.add(source)
        db_session.commit()

