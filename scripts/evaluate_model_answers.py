import spacy, csv, re
import pandas as pd
import Levenshtein
from difflib import SequenceMatcher
from sentence_transformers import SentenceTransformer, util
from utils.translator import translate

input_file = '../resources/csv_files/questions_with_answers_from_all_models.csv'
output_file = '../resources/csv_files/model_scores_v2.csv'

#Checks if there are greek letters in the string:
def is_translatable(string):
    for char in string:
        if char.isalpha() and re.search('[α-ωΑ-Ω]', char):
            return True
    return False

# Translates the string if it can.
def translate(string):
    if string not in greek_to_english.keys():
        if is_translatable(string):
            gr_string = string
            en_string = translate(string, "el", "en")
            print('Appending to dictionary:', gr_string, '->', en_string)
            greek_to_english[gr_string] = en_string  
            return en_string
        else:
            return string
    print('Using from dictionary:', string, '->', greek_to_english[string])
    return greek_to_english[string]


data = pd.read_csv(input_file, encoding='UTF-16')
model_answers = data['model_answer']
correct_answers = data['correct_answer']
questions = data['question']
models = data['model'][:10]
model_prediction_scores = data['score']

nlp = spacy.load("en_core_web_lg")
sentence_transformer = SentenceTransformer('distilbert-base-nli-mean-tokens')

headers = ['question', 'model', 'model_answer', 'correct_answer', 'model_prediction_score', 'nlp_score', 'levenshtein_score', 'substring_score', 'sentence_transformers_score', 'weighted_total_score']

greek_to_english = {}

with open(output_file, 'a', encoding='UTF16') as file:
    writer = csv.writer(file)
    writer.writerow(headers)
    print('Model answers count: ', len(model_answers))
    for i in range(int(len(model_answers) / 10)):
        write_format_flag = True
        weighted_scores = []
        for j in range(10):
            model_answer = translate(model_answers[i*10 + j])
            correct_answer = translate(correct_answers[i*10 + j])

            levenshtein_distance = Levenshtein.distance(model_answer, correct_answer)
            sentence_embeddings = sentence_transformer.encode([model_answer, correct_answer])
            
            #Calculate scores:
            nlp_score = float("{:.3f}".format(nlp(model_answer).similarity(nlp(correct_answer))))
            levenshtein_score = float("{:.3f}".format(1 - ( float(levenshtein_distance) / (max(len(model_answer), len(correct_answer))))))
            substring_score = float("{:.3f}".format(SequenceMatcher(None, model_answer, correct_answer).ratio()))
            sentence_transformers_score = float("{:.3f}".format(util.pytorch_cos_sim(sentence_embeddings[0], sentence_embeddings[1])[0][0].item()))

            weighted_score = nlp_score * 0.3 + levenshtein_score * 0.2 + substring_score * 0.2 + sentence_transformers_score * 0.3
            weighted_scores.append(weighted_score)

            if write_format_flag is True:
                writer.writerow([questions[i*10], models[j], model_answer, correct_answer, model_prediction_scores[i*10 + j], nlp_score, levenshtein_score, substring_score, sentence_transformers_score, weighted_score])
                write_format_flag = False           
            else:
                writer.writerow(['', models[j], model_answer, correct_answer, model_prediction_scores[i*10 + j], nlp_score, levenshtein_score, substring_score, sentence_transformers_score, weighted_score])