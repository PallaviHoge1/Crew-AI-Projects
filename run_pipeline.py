from src.pipeline.sequential_pipeline import run_pipeline
import os
from dotenv import load_dotenv
load_dotenv()

if __name__ == '__main__':
    SERPER_KEY = os.getenv('SERPER_API_KEY')
    topics = ['Pandas data manipulation', 'Exploratory Data Analysis with Python']
    run_pipeline(topics, serper_key=SERPER_KEY, level='beginner')
