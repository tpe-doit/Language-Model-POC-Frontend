from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy import Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Create a MetaData object for the database tables
Base = declarative_base()

# Define the User model class
class UserFeedback(Base):
    id = Column(Integer, primary_key=True)        # Auto-incrementing unique ID
    feedback = Column(Integer, nullable=False)    # Feedback, 0 if negative, 1 if positive.
    feedback_text = Column(String, nullable=True) # The feedback from user.
    user_prompt = Column(String, nullable=False)  # Current prompt given by the user.
    response = Column(String, nullable=False)     # The response generated by the model.

def feedback_insert(feedback, feedback_text, user_prompt, response):
    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()

    # Add a user feedback to the database
    user = UserFeedback(feedback=feedback, 
                        feedback_text=feedback_text, 
                        user_prompt=user_prompt, 
                        response=response)
    
    session.add(user)
    session.commit()


# Create a SQLite database engine
engine = create_engine("sqlite:///feedback.db")

# Create the users table
Base.metadata.create_all(engine)

if __name__ == "__main__":

    # Insert a user feedback
    feedback_insert(1, "Great job!", "Hello, how are you?", "I'm fine, thank you!")
    feedback_insert(0, "Not good.", "Why is the sky blue?", "Because I don't know.")


    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()

    # Query the database
    for user in session.query(UserFeedback):
        print(user.id, user.feedback, user.feedback_text, user.user_prompt, user.response)
