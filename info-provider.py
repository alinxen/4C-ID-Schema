from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import csv
import argparse
import sys


URI = "bolt://localhost:7687"
AUTH = ("neo4j", "DPif10mMAg54")

driver = GraphDatabase.driver(URI, auth=AUTH)
driver.verify_connectivity()

class LoadCourseData(): 
    _competence_dictionary = None
    _reverse_competence_dictionary = None
    _knowledge_dictionary = None
    _reverse_knowledge_dictionary = None
    _skill_dictionary = None
    _reverse_skill_dictionary = None
    _task_dictionary = None
    _reverse_task_dictionary = None
  
    @staticmethod
    def _make_knowledge_dictionary():
        m_cks = "import/competencies_knowledge_skills.csv"
        ID = "knowledge_id"
        name = "knowledge_title"

        dictionary = {}

        with open(m_cks, newline='', encoding='utf-8') as cks_file:
            reader = csv.DictReader(cks_file)
            dictionary = {
                row[ID] : row[name]
                for row in reader
            }
        
        return dictionary
    
    @classmethod
    def get_reverse_knowledge_dictionary(cls):
        if cls._reverse_knowledge_dictionary is None: 
            knowledge_dict = cls.get_knowledge_dictionary()
            cls._reverse_knowledge_dictionary = {name: id for id, name in knowledge_dict.items()}

        return cls._reverse_knowledge_dictionary

    @classmethod
    def get_knowledge_dictionary(cls):
        if cls._knowledge_dictionary is None:
            cls._knowledge_dictionary = LoadCourseData._make_knowledge_dictionary()
        return cls._knowledge_dictionary

    @staticmethod
    def _make_skill_dictionary():
        m_cks = "import/competencies_knowledge_skills.csv"
        ID = "skill_id"
        name = "skill_title"

        dictionary = {}

        with open(m_cks, newline='', encoding='utf-8') as cks_file:
            reader = csv.DictReader(cks_file)
            dictionary = {
                row[ID] : row[name]
                for row in reader
            }
        
        return dictionary
    
    @classmethod
    def get_reverse_skill_dictionary(cls):
        if cls._reverse_skill_dictionary is None:
            skill_dict = cls.get_skill_dictionary()
            cls._reverse_skill_dictionary = {name: id for id, name in skill_dict.items()}
        return cls._reverse_skill_dictionary

    @classmethod
    def get_skill_dictionary(cls):
        if cls._skill_dictionary is None:
            cls._skill_dictionary = LoadCourseData._make_skill_dictionary()
        return cls._skill_dictionary

    @staticmethod
    def _make_competence_dictionary():
        m_cks = "import/competencies_knowledge_skills.csv"
        ID = "competence_id"
        name = "competence_title"

        dictionary = {}

        with open(m_cks, newline='', encoding='utf-8') as cks_file:
            reader = csv.DictReader(cks_file)
            dictionary = {
                row[ID] : row[name]
                for row in reader
            }
            
            return dictionary
        
    @classmethod
    def get_reverse_competence_dictionary(cls):
        if cls._reverse_competence_dictionary is None:
            competence_dict = cls.get_competence_dictionary()
            cls._reverse_competence_dictionary = {name: id for id, name in competence_dict.items()}

        return cls._reverse_competence_dictionary

    @classmethod
    def get_competence_dictionary(cls):
        if cls._competence_dictionary is None:
            cls._competence_dictionary = LoadCourseData._make_competence_dictionary()
        return cls._competence_dictionary

    @staticmethod
    def _make_task_dictionary():
        m_hvp = "import/m_hvp.csv"

        dictionary = {}

        with open(m_hvp, newline='', encoding='utf-8') as hvp_file:
            reader = csv.DictReader(hvp_file)
            for row in reader:
                full_name = row.get('name', "").strip()
                key, value = full_name.split("", 1)
                dictionary[key] = value

        return dictionary

    @classmethod
    def get_task_dictionary(cls):
        if cls._task_dictionary is None:
            cls._task_dictionary = LoadCourseData._make_competence_dictionary()
            return cls._task_dictionary
                
#### Ausgabefunktionen
# Hilfsfunktionen für Ausgabefunktionen
def h_grammar_correction_task(number):
    if number == 1:
        return "1 Aufgabe "
    else:
        return (str(number) + " Aufgaben ")

def h_grammar_correction_attempt(number):
    if number == 1:
        return "ein Versuch "
    else:
        return (str(number) + " Versuche ")
    
def h_grammar_correction_student_nom(number):
    if number==1:
        return "1 Studierender "
    else:
        return (str(number) + " Studierende ")
    
def h_grammar_correction_student_dat(number):
    if number==1:
        return "einem Studierenden "
    else:
        return (str(number) + " Studierenden ")

def h_grammar_correction_haben(is_singular):
    if is_singular:
        return " hat "
    else:
        return " haben "

def h_grammar_correction_wurden(is_singular):
    if is_singular:
        return " wurde "
    else:
        return " wurden "

def h_grammar_correction_waren(is_singular):
    if is_singular:
        return " war "
    else:
        return " waren "

def h_normalize_duration(duration_record):
    seconds = duration_record.seconds
    hours = seconds//3600
    minutes = (seconds % 3600) // 60

    if hours==0:
        hours_print = " "
    elif hours==1:
        hours_print = " eine Stunde, "
    else:
        hours_print = " " + str(hours) + " Stunden, "

    if minutes==0:
        minutes_print = ""
    elif minutes==1:
        minutes_print= "eine Minute "
    else:
        minutes_print = str(minutes) + " Minuten "
    
    return(hours_print + minutes_print)


def h_change_minutes_to_hours(minutes_to_convert):
    if minutes_to_convert > 60:
        hours= int(minutes_to_convert//60)
        minutes=(minutes_to_convert%60)
        if hours==1:
            hours_print = "1 Stunde, "
        else:
            hours_print = str(hours) + " Stunden, "
        if minutes >0.5 and minutes <=1:
            minutes_print =" eine Minute"
        else:
            minutes_print = str(round(minutes)) + " Minuten"
        return(hours_print + minutes_print)
    else:
        if minutes_to_convert >0.5 and minutes_to_convert <=1:
            minutes_print = " eine Minute"
        else:
            minutes_print = str(round(minutes_to_convert, 1)) + " Minuten"
        return minutes_print

# liefert Skill-Namen für eine gegebene Skill-ID; gibt Skill-Namen oder leeren String zurück
def h_get_skill_name_for_id(skill_id):
    skill_items = LoadCourseData.get_skill_dictionary()
    if skill_id in skill_items:
        skill_name = skill_items[skill_id]
    else:
        print("Es scheint keine Fähigkeit mit dieser ID zu geben. Haben Sie sich vielleicht vertippt?")
        skill_name = ""
    return str(skill_name)

# liefert Skill-ID für einen gegebenen Skill-Namen; gibt Skill-ID oder leeren String zurück
def h_get_skill_id_for_name(skill_name):
    reverse_skill_items = LoadCourseData.get_reverse_skill_dictionary()
    if skill_name in reverse_skill_items:
        skill_id = reverse_skill_items[skill_name]
    else:
        print("Es scheint keine Fähigkeit mit diesem Namen zu geben. Haben Sie sich vielleicht vertippt?")
        skill_id = ""
    return str(skill_id)

# liefert Knowledge-Namen für eine gegebene Knowledge-ID; gibt Knowledge-Namen oder leeren String zurück
def h_get_knowledge_name_for_id(knowledge_id):
    knowledge_items = LoadCourseData.get_knowledge_dictionary()
    if knowledge_id in knowledge_items:
        knowledge_name = knowledge_items[knowledge_id]
    else:
        print("Es scheint kein Wissenselement mit dieser ID zu geben. Haben Sie sich vielleicht vertippt?")
        knowledge_name = ""
    return str(knowledge_name)

# liefert Knowledge-ID für eine gegebene Knowledge-ID; gibt Knowledge-ID oder leeren String zurück
def h_get_knowledge_id_for_name(knowledge_name):
    reverse_knowledge_items = LoadCourseData.get_reverse_knowledge_dictionary()
    if knowledge_name in reverse_knowledge_items:
        knowledge_id = reverse_knowledge_items[knowledge_name]
    else:
        print("Es scheint kein Wissenselement mit diesem Namen zu geben. Haben Sie sich vielleicht vertippt?")
        knowledge_id = ""
    return str(knowledge_id)

# liefert Competence-Namen für eine gegebene Competence-ID; gibt Competence-Namen oder leeren String zurück
def h_get_competence_name_for_id(competence_id):
    competence_items = LoadCourseData.get_competence_dictionary()
    if competence_id in competence_items:
        competence_name = competence_items[competence_id]
    else:
        print("Es scheint keine Kompetenz mit dieser ID zu geben. Haben Sie sich vielleicht vertippt?")
        competence_name = ""
    return str(competence_name)

# liefert Competence-ID für einen gegebenen Competence-Namen; gibt Competence-ID oder leeren String zurück
def h_get_competence_id_for_name(competence_name):
    reverse_competence_items = LoadCourseData.get_reverse_competence_dictionary()
    if competence_name in reverse_competence_items:
        competence_id = reverse_competence_items[competence_name]
    else:
        print("Es scheint keine Kompetenz mit diesem Namen zu geben. Haben Sie sich vielleicht vertippt?")
        competence_id = ""
    return str(competence_id)

def h_change_taxonomy_level_for_print(relation_name):
    if relation_name == 'remembers':
        return 'Erinnern'
    elif relation_name == 'understands':
        return 'Verstehen'
    elif relation_name == 'applies':
        return 'Anwenden'
    elif relation_name == 'analyzes':
        return 'Analysieren'
    elif relation_name == 'evaluates':
        return 'Bewerten'
    elif relation_name == 'creates':
        return 'Erstellen'

def h_change_knowledge_dimension_for_print(relation_name):
    if relation_name == 'needs_factual_knowledge':
        return 'Faktisches Wissen'
    elif relation_name == 'needs_procedural_knowledge':
        return 'Prozedurales Wissen'
    elif relation_name == 'needs_conceptual_knowledge':
        return 'Konzeptuelles Wissen'
    elif relation_name == 'needs_metacognitive_knowledge':
        return 'Metakognitives Wissen'
    
# liefert True, wenn der übergebene task_name einer Learning_Task entspricht, sonst False
def h_test_if_task(task_name):
    try:
        with driver.session() as session:
            params = {"task_name" : task_name}
            number_of_tasks_with_name = session.run("""
                MATCH (lt: Learning_Task {title: $task_name})
                RETURN COUNT(lt) AS NumberOfTasksWithName""", params).data()

        if number_of_tasks_with_name and number_of_tasks_with_name[0]['NumberOfTasksWithName'] == 1:
            return True
        else:
            return False
        
    except Neo4jError as e:
        print("Es gab ein Problem bei der Überprüfung, ob " + task_name + " eine Aufgabe im Kurs ist.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return False

# liefert True, wenn der übergebene im_name einer Informationsseite (Procedural Information oder Supportive Information) entspricht, sonst False
def h_test_if_im(im_name):
    try: 
        with driver.session() as session:
            params = {"im_name" : im_name}
            number_of_pages_with_name = session.run("""
                MATCH (im: Information_Material {title: $im_name})
                RETURN COUNT(im) AS NumberOfPagesWithName""", params).data()
            
        if number_of_pages_with_name and number_of_pages_with_name[0]['NumberOfPagesWithName'] == 1:
            return True
        else:
            return False
        
    except Neo4jError as e:
        print("Es gab ein Problem bei der Überprüfung, ob " + im_name + " eine Informationsseite im Kurs ist.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return False

# liefert True, wenn der übergebene last_name der Nachname eines im Kurs eingeschriebenen Studierenden ist, sonst False
def h_test_if_student(last_name):
    try:
        with driver.session() as session:
            params = {"last_name" : last_name}
            number_of_students_with_name = session.run("""
                MATCH (s:Student {last_name: $last_name})
                RETURN COUNT(s) AS NumberOfStudentsWithLastName""", params).data()
        
        if number_of_students_with_name and number_of_students_with_name[0]['NumberOfStudentsWithLastName'] == 1:
            return True
        else:
            return False
    
    except Neo4jError as e:
        print("Es gab ein Problem bei der Überprüfung, ob " + last_name + " ein im Kurs eingeschriebener Studierender ist.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return False

# gibt die (int-)Zahl der im Kurs eingeschriebenen Studierenden zurück
def h_get_number_of_enrolled_students():
    try:
        with driver.session() as session:
            number_of_students = session.run("""
                MATCH (s:Student)
                RETURN COUNT(s) AS ZahlStudierender""").data()
            
        if number_of_students and number_of_students[0]['ZahlStudierender'] is not None:
            return number_of_students[0]['ZahlStudierender']  
        else:
            return 0

    except Neo4jError as e:
        print("Es gab einen Fehler bei der Ermittlung der Zahl der Studierenden.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return 0
    
# gibt die (int-)Zahl der Learning Tasks im Kurs zurück
def h_get_number_of_learning_tasks():
    try:
        with driver.session() as session:
            number_of_tasks = session.run("""
                MATCH (lt:Learning_Task)
                RETURN COUNT(lt) AS ZahlAufgaben""").data()
        
        if number_of_tasks and number_of_tasks[0]['ZahlAufgaben'] is not None:
            return number_of_tasks[0]['ZahlAufgaben']
        else:
            return 0
           
    except Neo4jError as e:
        print("Es gab einen Fehler bei der Ermittlung der Zahl der Aufgaben im Kurs.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return 0

# gibt die (int-)Zahl der Procedural Information-Seiten im Kurs zurück
def h_get_number_of_pi():
    try:
        with driver.session() as session:
            number_of_tasks = session.run("""
                MATCH (pi: Procedural_Information)
                RETURN count(pi) AS AnzahlPI""").data()
        
        if number_of_tasks and number_of_tasks[0]['AnzahlPI'] is not None:
            return number_of_tasks[0]['AnzahlPI']
        else:
            return 0
           
    except Neo4jError as e:
        print("Es gab einen Fehler bei der Ermittlung der Zahl der Procedural Information-Seiten im Kurs.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return 0

# gibt die (int-)Zahl der Supportive Information-Seiten im Kurs zurück
def h_get_number_of_si():
    try:
        with driver.session() as session:
            number_of_tasks = session.run("""
                MATCH (si: Supportive_Information)
                RETURN count(si) AS AnzahlSI""").data()
        
        if number_of_tasks and number_of_tasks[0]['AnzahlSI'] is not None:
            return number_of_tasks[0]['AnzahlSI']
        else:
            return 0
           
    except Neo4jError as e:
        print("Es gab einen Fehler bei der Ermittlung der Zahl der Supportive Information-Seiten im Kurs.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return 0

# liefert als Rückgabewert einen Dataframe mit den Spalten Zeitpunkt, Material und DauerInMinuten, bei Fehler einen leeren Dataframe
def h_get_information_on_order(last_name):
    try:
        with driver.session() as session: 
            params = {"last_name" : last_name}
            order_of_student = session.run(""" 
            MATCH (s:Student {last_name: $last_name})-[:did_learning_session]-(:Learning_Session)-[c:covered]->(m)
            RETURN c.start_time AS Zeitpunkt, m.title AS Material, toInteger(round(c.time_spent)) AS DauerInMinuten ORDER BY Zeitpunkt""", params)
            data = [record.data() for record in order_of_student]
            if data:
                order = pd.DataFrame(data) 
                order['Zeitpunkt']=order['Zeitpunkt'].apply(lambda x: x.to_native() if hasattr(x, 'to_native') else x)
                return order
            else:
                print("Es gab ein Problem bei der Abfrage der Bearbeitungsreihenfolge von Herrn/Frau " + last_name)
                empty_df = pd.DataFrame()
                return empty_df
    
    except Neo4jError as e:
        print("Es gab ein Problem bei der Abfrage der Bearbeitungsreihenfolge von Herrn/Frau " + last_name)
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        empty_df = pd.DataFrame()
        return empty_df

# liefert als Rückgabewert zwei Dataframes: info_mat hat die Spalten "Lernsitzung" und "InfoMaterial" und listet pro Lernsitzung (ohne Dubletten) auf, welche
# Informationsseiten (Procedural Information und Supportive Information) wie lange bearbeitet wurden; tasks hat die Spalten "Lernsitzung" und "Aufgaben" und 
# listet pro Lernsitzung (ohne Dubletten) auf, welche Aufgaben wie lange bearbeitet wurden; bei Fehlern oder wenn kein Informationsmaterial bzw. keine Aufgaben
# bearbeitet wurden, werden zwei leere Dataframes zurückgegeben
def h_get_information_on_content(last_name):
    try:
        with driver.session() as session:
            params = {"last_name" : last_name}
            content_info_mat = session.run("""
                MATCH (s:Student {last_name: $last_name})-[:did_learning_session]-(ls:Learning_Session)
                MATCH (ls)-[c:covered]->(im:Information_Material)
                WITH ls.start_time AS Lernsitzung, im.title AS InfoMaterial, sum(c.time_spent) AS time_spent
                WITH Lernsitzung, COLLECT(DISTINCT {title: InfoMaterial, time_spent: time_spent}) AS InfoMaterial
                RETURN Lernsitzung, InfoMaterial""", params)
            content_tasks = session.run("""
                MATCH (s:Student {last_name: $last_name})-[:did_learning_session]-(ls:Learning_Session)
                MATCH (ls)-[c:covered]->(lt:Learning_Task)
                WITH ls.start_time AS Lernsitzung, lt.title AS Aufgaben, sum(c.time_spent) AS time_spent
                WITH Lernsitzung, COLLECT(DISTINCT {title: Aufgaben, time_spent: time_spent}) AS Aufgaben
                RETURN Lernsitzung, Aufgaben""", params)
            data_info_mat = [record.data() for record in content_info_mat]
            if data_info_mat:
                info_mat = []
                for session in data_info_mat:
                    for material in session['InfoMaterial']:
                        info_mat.append({
                            'Lernsitzung': session['Lernsitzung'],
                            'InfoMaterial' : material['title'],
                            'ZeitInMinuten' : round(material['time_spent'], 1)
                        })
                df_info_mat = pd.DataFrame(info_mat) if info_mat else pd.DataFrame()
                df_info_mat["Lernsitzung"] = df_info_mat["Lernsitzung"].apply(lambda x: x.to_native() if hasattr(x, 'to_native') else x)             

            else:
                df_info_mat = pd.DataFrame()
                
            data_tasks = [record.data() for record in content_tasks]
            if data_tasks:
                tasks = []
                for session in data_tasks:
                    for task in session['Aufgaben']:
                        tasks.append({
                            'Lernsitzung' : session['Lernsitzung'],
                            'Aufgabe' : task['title'],
                            'ZeitInMinuten' : round(task['time_spent'], 1)
                        })
                df_tasks = pd.DataFrame(tasks) if tasks else pd.DataFrame()
                df_tasks["Lernsitzung"] = df_tasks["Lernsitzung"].apply(lambda x: x.to_native() if hasattr(x, 'to_native') else x)           
            else:
                df_tasks = pd.DataFrame()
                
            return df_info_mat, df_tasks
    
    except Neo4jError as e:
        print("Es gab ein Problem bei der Abfrage der Bearbeitungsreihenfolge von Herrn/Frau " + last_name)
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        empty_df = pd.DataFrame()
        return empty_df, empty_df

##
# gibt das letzte Ergebnis (als int) des Studierenden für die angegebene Aufgabe aus
def h_get_students_last_result_for_task(last_name, task_title):
    try:
        with driver.session() as session:
            params = {"last_name" : last_name, "task_title" : task_title}
            score = session.run("""
                MATCH(s:Student {last_name: $last_name})-[c:completed]-(ls:Learning_Task {title: $task_title})
                RETURN c.score AS Punktzahl""", params).data()
            
        if score and score[0]['Punktzahl'] is not None:
            Punktzahl = round(score[0]['Punktzahl'], 1)
            return Punktzahl
        else:
            return 0

    except Neo4jError as e:
        print("Es ist ein Fehler bei der Ermittlung des letzten Ergebnisses für die Aufgabe " + task_title + " aufgetaucht.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return 0

# gibt die letzte eingereichte Antwort des Studierenden für die angegebene Aufgabe aus, sonst leeren String
def h_get_students_last_response_for_task(last_name, task_title):
    try:
        with driver.session() as session:
            params = {"last_name" : last_name, "task_title" : task_title}
            response = session.run("""
                MATCH(s:Student {last_name: $last_name})-[r:struggled_with|successfully_solved]-(ls:Learning_Task {title: $task_title})
                WITH r.timestamp AS ZeitpunktDesLösungsversuchs, r.student_response AS Antwortvorschlag
                RETURN ZeitpunktDesLösungsversuchs, Antwortvorschlag ORDER BY ZeitpunktDesLösungsversuchs DESC LIMIT 1""", params).data()

        if response and response[0]['Antwortvorschlag'] is not None:
            return (response[0]['Antwortvorschlag'])
        else:
            return "" 
    
    except Neo4jError as e:
        print("Es ist ein Fehler bei der Ermittlung der Antworten des Studierenden für die Aufgabe " + task_title + " aufgetaucht.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return ""

# gibt die Anzahl der erfolgreichen Lösungsversuche (int) zurück, die ein Studierender für eine Aufgabe unternommen hat
def h_get_number_of_successful_attempts_for_task_and_student(last_name, task_title):
    try:
        with driver.session() as session:
            params = {"last_name" : last_name, "task_title" : task_title}
            score = session.run("""
                MATCH(s:Student {last_name: $last_name})-[r:successfully_solved]-(ls:Learning_Task {title: $task_title})
                RETURN count(r) AS AnzahlErfolgreicherVersuche""", params).data()
            
        if score and score[0]['AnzahlErfolgreicherVersuche'] is not None:
            number_of_successful_attempts = score[0]['AnzahlErfolgreicherVersuche']
            return number_of_successful_attempts
        else:
            return 0

    except Neo4jError as e:
        print("Es ist ein Problem bei der Ermittlung der Zahl der erfolgreichen Lösungsversuche für die Aufgabe " + task_title + " aufgetreten.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return 0
        
##
# gibt die Gesamtnzahl der Lösungsversuche (int) für eine Aufgabe zurück
def h_get_number_of_attempts_for_task(task_name):
    try:
        with driver.session() as session:
            params = {"task_name" : task_name}
            number_of_successful_attempts= session.run("""
                        MATCH ()-[r:successfully_solved|struggled_with]->(lt:Learning_Task {title: $task_name})
                        RETURN COUNT(r) AS ZahlVersuche""", params).data()
    
        if number_of_successful_attempts and number_of_successful_attempts[0]['ZahlVersuche'] is not None:
            return number_of_successful_attempts[0]['ZahlVersuche']
        else:
            return 0
    
    except Neo4jError as e:
        print("Es ist ein Fehler bei der Ermittlung der Anzahl der Lösungsversuche für Aufgabe " + task_name + " aufgetreten.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return 0

# gibt die Gesamtzahl der erfolgreichen Lösungsversuche (int) für eine Aufgabe zurück
def h_get_number_of_successful_attempts_for_task(task_name):
    try:
        with driver.session() as session:
            params = {"task_name" : task_name}
            number_of_successful_attempts= session.run("""
                        MATCH ()-[r:successfully_solved]->(lt:Learning_Task {title: $task_name})
                        RETURN COUNT(r) AS ZahlVersuche""", params).data()
    
        if number_of_successful_attempts and number_of_successful_attempts[0]['ZahlVersuche'] is not None:
            return number_of_successful_attempts[0]['ZahlVersuche']
        else:
            return 0
    
    except Neo4jError as e:
        print("Es ist ein Fehler bei der Ermittlung der Anzahl der erfolgreichen Lösungsversuche für Aufgabe " + task_name + " aufgetreten.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return 0

# gibt die Gesamtnzahl der Lösungsversuche (int) mit weniger als 80 Prozent der Punkte für eine Aufgabe zurück
def h_get_number_of_attempts_with_difficulties_for_task(task_name):
    try:
        with driver.session() as session:
            params = {"task_name" : task_name}
            number_of_attempts_with_difficulties = session.run("""
                MATCH ()-[r:struggled_with]->(lt:Learning_Task {title: $task_name}) 
                RETURN COUNT(r) AS ZahlVersucheMitProblemen""", params).data()  

        if number_of_attempts_with_difficulties and number_of_attempts_with_difficulties[0]['ZahlVersucheMitProblemen'] is not None:
            return number_of_attempts_with_difficulties[0]['ZahlVersucheMitProblemen']
        else:
            return 0
    
    except Neo4jError as e:
        print("Es ist ein Fehler bei der Ermittlung der Anzahl der Lösungsversuche mit weniger als 80 Prozent der Punkte für Aufgabe " + task_name + " aufgetreten.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return 0


# gibt falsche Antworten zurück, die bei der Aufgabe eingereicht wurden, sonst einen leeren String
def h_get_wrong_answers_for_task(task_name):
    text_about_wrong_answers = ""
    try:
        wrong_answers = []
        with driver.session() as session:
            params = {"task_name" : task_name}
            wrong_answers_records = session.run("""
                MATCH (s:Student)-[r:struggled_with]->(lt:Learning_Task {title: $task_name})
                RETURN DISTINCT r.student_response AS FalscheAntworten, lt.type AS Aufgabentyp""", params).data()
        
        if wrong_answers_records:
            for record in wrong_answers_records:
                if record['FalscheAntworten'] is None:
                    if record['Aufgabentyp']=="Multiple Choice" or record['Aufgabentyp']=="Drag and Drop":
                        wrong_answers.append("leere Abgabe")
                else:
                    wrong_answers.append(record['FalscheAntworten'])    
            if wrong_answers != []:
                text_about_wrong_answers = text_about_wrong_answers + "\nFalsche Antworten, die für Aufgabe " + task_name + " abgegeben wurden, waren beispielsweise : \n -" + (" \n- ".join(wrong_answers)) + ".\n"

    except Neo4jError as e:
        print("Es ist ein Problem bei der Ermittlung der falschen Antworten für die Aufgabe " + task_name + " aufgetreten.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)

    return text_about_wrong_answers
    
# gibt das durchschnittliche Ergebnis für eine Lernaufgabe (float, auf eine Stelle gerundet) zurück
def h_get_average_result_for_task(task_name):
    try:
        with driver.session() as session:
            params = {"task_name" : task_name}
            average_result = session.run("""
            MATCH()-[r:successfully_solved|struggled_with]->(lt:Learning_Task {title: $task_name})
            RETURN AVG(r.score) AS DurchschnittlichesErgebnis""", params).data() 

        if average_result and average_result[0]['DurchschnittlichesErgebnis'] is not None:
            return round(average_result[0]['DurchschnittlichesErgebnis'],1)
        else:
            return 0

    except Neo4jError as e:
        print("Es ist ein Problem bei der Ermittlung des Durchschnittsergebnisses für die Aufgabe " + task_name + " aufgetreten.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return 0

# gibt die Anzahl von Studierenden zurück, die im ersten Lösungsversuch zu einer Aufgabe die volle Punktzahl erreicht haben
def h_get_number_of_students_with_perfect_record_for_task(task_name):
    try:
        with driver.session() as session:   
            params = {"task_name" : task_name}
            number_of_students_with_perfect_record = session.run("""
                MATCH (s: Student)-[r:successfully_solved|struggled_with]->(lt:Learning_Task {title: $task_name})
                WITH s, r, lt
                ORDER BY r.timestamp
                WITH s, lt, COLLECT(r)[0] AS ErsterVersuch
                WHERE ErsterVersuch.score = 10
                RETURN COUNT(s) AS ZahlStudierenderMitVollerPunktzahlImErstenVersuch""", params).data()
            
        if number_of_students_with_perfect_record and number_of_students_with_perfect_record[0]['ZahlStudierenderMitVollerPunktzahlImErstenVersuch'] is not None:
            return number_of_students_with_perfect_record[0]['ZahlStudierenderMitVollerPunktzahlImErstenVersuch']
        else:
            return 0
     
    except Neo4jError as e:
        print("Es ist ein Problem bei der Ermittlung der Anzahl der Studierenden aufgetreten, die bei Aufgabe " + task_name + " im ersten Versuch die volle Punktzahl erzielt haben.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return 0

# gibt die durchschnittlich mit einer Aufgabe verbrachte Zeit (float, gerundet auf eine Nachkommastelle) in Minuten zurück
def h_get_average_time_spent_on_task(task_name):
    try:
        with driver.session() as session:   
            params = {"task_name" : task_name}
            average_time_spent_on_task = session.run("""
                MATCH (s:Student)-[]->(ls:Learning_Session)-[c:covered]->(lt:Learning_Task {title: $task_name}) 
                WITH s, SUM(c.time_spent) AS timeSpentPerPerson
                RETURN AVG(timeSpentPerPerson) AS DurchschnittlichVerbrachteZeit""", params).data()  

        if average_time_spent_on_task and average_time_spent_on_task[0]['DurchschnittlichVerbrachteZeit'] is not None:
            return round(average_time_spent_on_task[0]['DurchschnittlichVerbrachteZeit'], 1)
        else:
            return 0

    except Neo4jError as e:
        print("Es ist ein Problem bei der Ermittlung der durchschnittlich mit der Aufgabe " + task_name + " verbrachten Zeit aufgetaucht.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return 0
    
# gibt die insgesamt mit einer Aufgabe verbrachte Zeit (float, gerundet auf eine Nachkommastelle) in Minuten zurück
def h_get_total_time_spent_on_task(task_name):
    try:
        with driver.session() as session:   
            params = {"task_name" : task_name}
            total_time_spent_on_task = session.run("""
                MATCH (s:Student)-[]->(ls:Learning_Session)-[c:covered]->(lt:Learning_Task {title: $task_name}) 
                RETURN SUM(c.time_spent) AS Gesamtzeit""", params).data()  
            
            if total_time_spent_on_task and total_time_spent_on_task[0]['Gesamtzeit'] is not None:
                return round(total_time_spent_on_task[0]['Gesamtzeit'], 1)
            else:
                return 0

    except Neo4jError as e:
        print("Es ist ein Problem bei der Ermittlung der insgesamt mit der Aufgabe " + task_name + " verbrachten Zeit aufgetaucht.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return 0
    
# gibt die insgesamt mit einer Aufgabe verbrachte Zeit (float, gerundet auf eine Nachkommastelle) in Minuten zurück
def h_get_total_time_spent_on_im(im_name):
    try:
        with driver.session() as session:   
            params = {"im_name" : im_name}
            total_time_spent_on_im = session.run("""
                MATCH (s:Student)-[]->(ls:Learning_Session)-[c:covered]->(im: Information_Material {title: $im_name}) 
                RETURN SUM(c.time_spent) AS Gesamtzeit""", params).data()  
            
            if total_time_spent_on_im and total_time_spent_on_im[0]['Gesamtzeit'] is not None:
                return round(total_time_spent_on_im[0]['Gesamtzeit'], 1)
            else:
                return 0

    except Neo4jError as e:
        print("Es ist ein Problem bei der Ermittlung der insgesamt mit der Infoseite " + im_name + " verbrachten Zeit aufgetaucht.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return 0
    
# gibt die Anzahl der Aufgaben zurück, die ohne Lösungsversuch als abgeschlossen markiert wurden
def h_get_number_of_completed_without_attempts(task_name):
    try:
        with driver.session() as session:   
            params = {"task_name" : task_name}
            number_of_completed_without_attempts = session.run("""
                MATCH (s:Student)-[c:completed]->(lt:Learning_Task {title: $task_name})
                WHERE NOT EXISTS {(s)-[r:successfully_solved|struggled_with]->(lt)}
                RETURN COUNT(*) AS ZahlStudierender""", params).data()
            
            if number_of_completed_without_attempts and number_of_completed_without_attempts[0]['ZahlStudierender'] is not None:
                return number_of_completed_without_attempts[0]['ZahlStudierender']
            else:
                return 0

    except Neo4jError as e:
        print("Es ist ein Problem bei der Ermittlung der Anzahl der Aufgaben aufgetreten, die ohne Lösungsversuch als abgeschlossen markiert wurden.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return 0
    
# gibt die Anzahl der Studierenden zurück, die eine Aufgabe bearbeitet haben
def h_get_number_of_students_covering_task(task_name):
    try:
        with driver.session() as session:   
            params = {"task_name" : task_name}
            number_of_students = session.run("""
                MATCH(s:Student)-[r]->(ls:Learning_Session)-[co:covered]->(lt:Learning_Task {title: $task_name})
                RETURN COUNT(DISTINCT s)AS ZahlStudenten""", params).data() 
            
        if number_of_students and number_of_students[0]['ZahlStudenten'] is not None:
            return number_of_students[0]['ZahlStudenten']
        else:
            return 0 
     
    except Neo4jError as e:
        print("Es gab einen Fehler bei der Berechnung der Anzahl der Studierenden, die eine Aufgabe bearbeitet haben.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return 0
    
# gibt die Anzahl der Studierenden zurück, die zu einer Aufgabe mindestens einen Lösungsversuch abgegeben haben
def h_get_number_of_students_making_attempt_for_task(task_name):
    try:
        with driver.session() as session:   
            params = {"task_name" : task_name}
            number_of_students = session.run("""
                MATCH(s:Student)-[r:struggled_with|successfully_solved]->(lt:Learning_Task {title: $task_name})
                RETURN COUNT(DISTINCT s) AS ZahlStudenten""", params).data() 
        
        if number_of_students and number_of_students[0]['ZahlStudenten'] is not None:
            return number_of_students[0]['ZahlStudenten']
        else:
            return 0
     
    except Neo4jError as e:
        print("Es ist ein Fehler bei der Ermittlung der Anzahl von Studierenden aufgetreten, die einen Lösungsversuch für Aufgabe " + task_name + " unternommen haben.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return 0

##
# gibt die durchschnittlich mit einer Informationsseite verbrachte Zeit (float, gerundet auf eine Nachkommastelle) in Minuten zurück
def h_get_average_time_spent_on_im(im_name):
    try:
        with driver.session() as session:   
            params = {"im_name" : im_name}
            average_time_spent_on_im = session.run("""
                MATCH (s:Student)-[]->(ls:Learning_Session)-[c:covered]->(im:Information_Material {title: $im_name}) 
                WITH s, SUM(c.time_spent) AS timeSpentPerPerson
                RETURN AVG(timeSpentPerPerson) AS DurchschnittlichVerbrachteZeit""", params).data()
    
        if average_time_spent_on_im and average_time_spent_on_im[0]['DurchschnittlichVerbrachteZeit'] is not None:
            return round(average_time_spent_on_im[0]['DurchschnittlichVerbrachteZeit'], 1)
        else:
            return 0
    
    except Neo4jError as e:
        print("Es ist ein Fehler bei der Ermittlung der durchschnittlich mit dem Informationsmaterial " + im_name + " verbrachten Zeit aufgetreten.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return 0

# gibt Informationen (Text) über die Kompetenzen zurück, die in einer Aufgabe unterrichtet werden
def h_get_competences_taught_in_task(task_name):
    try:
        with driver.session() as session:   
            params = {"task_name" : task_name}
            number_of_competences_taught_in_task = session.run("""
                MATCH(c:Competence)-[r]->(lt:Learning_Task {title: $task_name})
                RETURN COUNT(c) AS AnzahlKompetenzen""", params).data() 
            competences_taught_in_task = session.run("""
                MATCH(c:Competence)-[r]->(lt:Learning_Task {title: $task_name})
                RETURN c.title AS Kompetenz, c.co_ID AS ID""", params).data() 
        
        text_to_print = ""
        if number_of_competences_taught_in_task and number_of_competences_taught_in_task[0]['AnzahlKompetenzen'] is not None and competences_taught_in_task and competences_taught_in_task[0]['Kompetenz'] is not None:
            number_of_competences = number_of_competences_taught_in_task[0]['AnzahlKompetenzen']
            if number_of_competences == 0:
                text_to_print = text_to_print + "Im Rahmen der Aufgabe " + task_name + " werden keine Kompetenzen unterrichtet."
            else:
                competence_list = []
                for record in competences_taught_in_task: 
                    competence_list.append(record['Kompetenz'] + " [" + record['ID'] + "]")
                if len(competence_list) == 1:
                    text_to_print = text_to_print + "Im Rahmen der Aufgabe " + task_name + " wird die Kompetenz " + competence_list[0] + " unterrichtet. "
                elif len(competence_list) > 1:
                    text_to_print = text_to_print + "Im Rahmen der Aufgabe " + task_name + " werden die " + str(number_of_competences) + " Kompetenzen " + (", ".join(competence_list)) + " unterrichtet. "
        
        return text_to_print
    
    except Neo4jError as e:
        print("Es ist ein Fehler bei der Ermittlung der Kompetenzen aufgetreten, die im Rahmen der Aufgabe " + task_name + " unterrichtet werden.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return 0

# gibt Informationen (Text) über die Fähigkeiten zurück, die für eine Aufgabe erforderlich sind (inklusive kognitiver Prozesse)
def h_get_skills_taught_in_task(task_name):
    try:
        with driver.session() as session:   
            params = {"task_name" : task_name}
            number_of_skills_taught_in_task = session.run("""
                MATCH(s:Skill)<-[r]-(lt:Learning_Task {title: $task_name})
                RETURN COUNT(s) AS AnzahlFähigkeiten""", params).data() 
            skills_taught_in_task = session.run("""
                MATCH(s:Skill)<-[r]-(lt:Learning_Task {title: $task_name})
                RETURN s.title AS Fähigkeit, s.sk_ID AS ID, type(r) AS kognitiverProzess""", params).data() 
        
        text_to_print = ""
        if number_of_skills_taught_in_task and number_of_skills_taught_in_task[0]['AnzahlFähigkeiten'] is not None and skills_taught_in_task and skills_taught_in_task[0]['Fähigkeit'] is not None:
            number_of_skills = number_of_skills_taught_in_task[0]['AnzahlFähigkeiten']
            if number_of_skills == 0:
                text_to_print = text_to_print + "Im Rahmen der Aufgabe " + task_name + " werden keine Fähigkeiten unterrichtet."
            else:
                skill_list = []
                for record in skills_taught_in_task: 
                    taxonomy_level = h_change_taxonomy_level_for_print(record['kognitiverProzess'])
                    skill_list.append(record['Fähigkeit'] + " [" + record['ID'] + "] auf der Taxonomiestufe \"" + taxonomy_level + "\"")
                if len(skill_list) >= 1:
                    text_to_print = text_to_print + "Im Rahmen der Aufgabe " + task_name + " werden die folgenden Fähigkeiten unterrichtet:\n" + "\n".join([f"- {skill}" for skill in skill_list])
        
        return text_to_print
    
    except Neo4jError as e:
        print("Es ist ein Fehler bei der Ermittlung der Fähigkeiten aufgetreten, die im Rahmen der Aufgabe " + task_name + " unterrichtet werden.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return 0

# gibt Informationen (Text) über die Wissenselemente zurück, die für eine Aufgabe erforderlich sind (inklusive Wissensdimensionen)
def h_get_knowledge_taught_in_task(task_name):
    try:
        with driver.session() as session:   
            params = {"task_name" : task_name}
            number_of_knowledge_items_taught_in_task = session.run("""
                MATCH(k:Knowledge)<-[r]-(lt:Learning_Task {title: $task_name})
                RETURN COUNT(k) AS AnzahlWissenselemente""", params).data() 
            knowledge_items_taught_in_task = session.run("""
                MATCH(k:Knowledge)<-[r]-(lt:Learning_Task {title: $task_name})
                RETURN k.title AS Wissenselement, k.kn_ID AS ID, type(r) AS Wissensdimension""", params).data() 
        
        text_to_print = ""
        if number_of_knowledge_items_taught_in_task and number_of_knowledge_items_taught_in_task[0]['AnzahlWissenselemente'] is not None and knowledge_items_taught_in_task and knowledge_items_taught_in_task[0]['Wissenselement'] is not None:
            number_of_knowledge_items = number_of_knowledge_items_taught_in_task[0]['AnzahlWissenselemente']
            if number_of_knowledge_items == 0:
                text_to_print = text_to_print + "Im Rahmen der Aufgabe " + task_name + " werden keine Wissenselemente unterrichtet."
            else:
                knowledge_list = []
                for record in knowledge_items_taught_in_task: 
                    taxonomy_level = h_change_knowledge_dimension_for_print(record['Wissensdimension'])
                    knowledge_list.append(record['Wissenselement'] + " [" + record['ID'] + "] in der Wissensdimension \"" + taxonomy_level + "\"")
                if len(knowledge_list) >= 1:
                    text_to_print = text_to_print + "Im Rahmen der Aufgabe " + task_name + " werden die folgenden Wissenselemente unterrichtet:\n" + "\n".join([f"- {knowledge}" for knowledge in knowledge_list])
        
        return text_to_print
    
    except Neo4jError as e:
        print("Es ist ein Fehler bei der Ermittlung der Wissenselemente aufgetreten, die im Rahmen der Aufgabe " + task_name + " unterrichtet werden.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return 0

##
# nutzt einen Degree Centrality-Algorithmus, um zu ermitteln, mit welchen Kompetenzen / Wissenselementen / Fähigkeiten am meisten Zeit verbracht wurde
# gibt Informationen in Textform zurück
def get_practice_of_competence_knowledge_skill():
    try:
        with driver.session() as session:
            # Projektion erstellen, in der Student-Knoten mit Kompetenz-Knoten verbunden werden, wenn sie eine Übung bearbeitet haben, die diese Kompetenz vermittelt,
            # und in der als Gewichtung die mit der Übung verbrachte Zeit verwendet wird
            session.run("""
                CALL gds.graph.drop('student-competences', false)
                YIELD graphName""")
            session.run("""
                MATCH(source:Student)-[:did_learning_session]->(:Learning_Session)-[r:covered]->(:Learning_Task)<-[:is_taught_by]-(target:Competence)
                RETURN gds.graph.project(
                    'student-competences',
                    target,
                    source,
                    {relationshipProperties: r {.time_spent}},
                    {})""")
            # Centrality-Algorithmus auf der Projektion laufen lassen
            competence_centrality = session.run("""
                CALL gds.degree.stream(
                    'student-competences',
                    {relationshipWeightProperty: 'time_spent'}
                )
                YIELD nodeId, score
                RETURN gds.util.asNode(nodeId).title AS Competence, score AS Score ORDER BY Score DESC LIMIT 3
                """).data()
            # Projektion erstellen, in der Student-Knoten mit Wissens-Knoten verbunden werden, wenn sie eine Übung bearbeitet haben, die dieses Wissen vermittelt,
            # und in der als Gewichtung die mit der Übung verbrachte Zeit verwendet wird
            session.run("""
                CALL gds.graph.drop('student-knowledge', false)
                YIELD graphName""")
            session.run("""
                MATCH(source:Student)-[:did_learning_session]->(:Learning_Session)-[r:covered]->(:Learning_Task)-[s]->(target:Knowledge)
                RETURN gds.graph.project(
                    'student-knowledge',
                    target,
                    source,
                    {relationshipProperties: r {.time_spent}},
                    {})""")
            # Centrality-Algorithmus auf der Projektion laufen lassen
            knowledge_centrality = session.run("""
                CALL gds.degree.stream(
                    'student-knowledge',
                    {relationshipWeightProperty: 'time_spent'}
                )
                YIELD nodeId, score
                RETURN gds.util.asNode(nodeId).title AS Knowledge, score AS Score ORDER BY Score DESC LIMIT 3
                """).data()
            # Projektion erstellen, in der Student-Knoten mit Fähigkeits-Knoten verbunden werden, wenn sie eine Übung bearbeitet haben, die diese Fähigkeit vermittelt,
            # und in der als Gewichtung die mit der Übung verbrachte Zeit verwendet wird
            session.run("""
                CALL gds.graph.drop('student-skill', false)
                YIELD graphName""")
            session.run("""
                MATCH(source:Student)-[:did_learning_session]->(:Learning_Session)-[r:covered]->(:Learning_Task)-[s]->(target:Skill)
                RETURN gds.graph.project(
                    'student-skill',
                    target,
                    source,
                    {relationshipProperties: r {.time_spent}},
                    {})""")
            # Centrality-Algorithmus auf der Projektion laufen lassen
            skill_centrality = session.run("""
                CALL gds.degree.stream(
                    'student-skill',
                    {relationshipWeightProperty: 'time_spent'}
                )
                YIELD nodeId, score
                RETURN gds.util.asNode(nodeId).title AS Skill, score AS Score ORDER BY Score DESC LIMIT 3
                """).data()
            
            text = ""
            if competence_centrality:
                for i in range(3):
                    if competence_centrality[i]['Competence'] is not None and competence_centrality[i]['Score'] is not None:
                        text = text + "- Kompetenz " + competence_centrality[i]['Competence'] + "\n"
                for i in range(3):
                    if knowledge_centrality[i]['Knowledge'] is not None and knowledge_centrality[i]['Score'] is not None:
                        text = text + "- Wissenselement " + knowledge_centrality[i]['Knowledge'] + "\n"
                for i in range(3):
                    if skill_centrality[i]['Skill'] is not None and skill_centrality[i]['Score'] is not None:
                        text = text + "- Fähigkeit " + skill_centrality[i]['Skill'] + "\n"

        driver.execute_query("""
            CALL gds.graph.drop('student-competences', false)
            YIELD graphName""")
        driver.execute_query("""
            CALL gds.graph.drop('student-knowledge', false)
            YIELD graphName""")
        driver.execute_query("""
            CALL gds.graph.drop('student-skill', false)
            YIELD graphName""")

        return text

    except Neo4jError as e:
        text = "In der Funktion zur Ermittlung der Kompetenzen / Wissenselemente / Fähigkeiten, mit denen am meisten Zeit verbracht wurde, ist leider ein Neo4j-Fehler aufgetreten.\n"
        text = text + "Neo4j error code: " + str(e.code)
        if e.message is not None:
            text = text + "Exception message: " + e.message
        return text

# gibt Informationen (Text) darüber zurück, in wie vielen und welchen Aufgaben eine Kompetenz vermittelt wird und wie viele Studierenden diese Aufgaben mit welchem Erfolg bearbeitet haben
def h_get_information_on_competence(competence_id):
    competence_name = h_get_competence_name_for_id(competence_id)
    if competence_name == "":
        # Fehlermeldung schon in Funktion ausgegeben
        return

    text_to_print = ""
    try:
        with driver.session() as session:   
            params = {"competence_id" : competence_id}
            number_of_tasks = session.run("""
                MATCH (c:Competence {co_ID: $competence_id})-[t:is_taught_by]->(lt:Learning_Task)
                RETURN COUNT(lt) AS ZahlAufgaben""", params).data() 
            tasks = session.run("""
                MATCH (c:Competence {co_ID: $competence_id})-[t:is_taught_by]->(lt:Learning_Task)
                RETURN lt.title AS Aufgabe""", params).data() 
        
        if number_of_tasks and number_of_tasks[0]['ZahlAufgaben'] is not None:
            number_of_tasks_teaching_competence = number_of_tasks[0]['ZahlAufgaben']
        else:
            number_of_tasks = 0
            text_to_print = "Diese Kompetenz wird in dieser Lerneinheit nicht vermittelt. Oder haben Sie sich vielleicht vertippt?"
            return(text_to_print)
        
        task_list = []
        if tasks:
            for record in tasks:
                task_list.append(record['Aufgabe'])
            task_list.sort()
        
        if number_of_tasks != 0:
            text_to_print = "Die Kompetenz \"" + competence_name + "\" wird in insgesamt " + h_grammar_correction_task(number_of_tasks_teaching_competence) + "vermittelt, und zwar in: " + (", ".join(task_list)) + ".\n\n"
        
            for task in task_list:
                task_name = str(task)
                number_of_students = h_get_number_of_students_covering_task(task_name)
                number_of_students_doing_attempt = h_get_number_of_students_making_attempt_for_task(task_name)
                number_of_attempts = h_get_number_of_attempts_for_task(task_name)
                number_of_successful_attempts = h_get_number_of_successful_attempts_for_task(task_name)
                average_time = h_get_average_time_spent_on_task(task_name)
                total_time = h_get_total_time_spent_on_task(task_name)
                total_time_print = h_change_minutes_to_hours(total_time)

                text_to_print = text_to_print + " - Aufgabe \"" + str(task) + "\" wurde von " + h_grammar_correction_student_dat(number_of_students) + "bearbeitet und " + h_grammar_correction_student_nom(number_of_students_doing_attempt) + h_grammar_correction_haben(number_of_students_doing_attempt==1) + "einen Lösungsversuch unternommen. "
                if number_of_attempts == 1:
                    text_to_print = text_to_print + "Der eine Lösungsversuch"
                    if number_of_successful_attempts==1:
                        text_to_print = text_to_print + " war erfolgreich (über 80 Prozent der Punkte erreicht). "
                    else: 
                        text_to_print = text_to_print + " war nicht erfolgreich (weniger als 80 Prozent der Punkte). "
                elif number_of_attempts > 1:
                    text_to_print = text_to_print + "Von den insgesamt " + str(number_of_attempts) + " Lösungsversuchen" + h_grammar_correction_waren (number_of_successful_attempts==1) + str(number_of_successful_attempts) + " erfolgreich (mindestens 80 Prozent der Punkte). "
                text_to_print = text_to_print + "Durchschnittlich wurden " + str(average_time) + " Minuten mit der Aufgabe verbracht und insgesamt " + total_time_print + ". \n"

    except Neo4jError as e:
        text_to_print = "Es ist ein Fehler beim Einholen von Informationen über die Kompetenz \"" + competence_name + "\" aufgetreten."
        text_to_print = text_to_print + "Neo4j error code: " + str(e.code) + "; "
        if e.message is not None:
            text_to_print = text_to_print + "Exception message: " + e.message

    return text_to_print

# gibt Informationen (Text) darüber zurück, in wie vielen und welchen Aufgaben ein Wissenselement vermittelt wird und wie viele Studierenden diese Aufgaben mit welchem Erfolg bearbeitet haben
def h_get_information_on_knowledge(knowledge_id):
    knowledge_name = h_get_knowledge_name_for_id(knowledge_id)
    if knowledge_name == "":
        # Fehlermeldung schon in Funktion ausgegeben
        return

    text_to_print = ""
    try:
        with driver.session() as session:   
            params = {"knowledge_id" : knowledge_id}
            total_number_of_tasks = session.run("""
                MATCH (k:Knowledge {kn_ID: $knowledge_id})<-[r]-(lt:Learning_Task)
                RETURN COUNT(DISTINCT lt) AS ZahlAufgaben""", params).data() 
            number_of_tasks_knowledge_dimensions = session.run("""
                MATCH (k:Knowledge {kn_ID: $knowledge_id})<-[r]-(lt:Learning_Task)
                RETURN type(r) AS Wissensdimension, COUNT(DISTINCT lt) AS ZahlAufgaben""", params).data()
            tasks_knowledge_dimensions = session.run("""
                MATCH (k:Knowledge {kn_ID: $knowledge_id})<-[r]-(lt:Learning_Task)
                RETURN type(r) AS Wissensdimension, lt.title AS Aufgabe""", params).data()
        
        if total_number_of_tasks and total_number_of_tasks[0]['ZahlAufgaben'] is not None:
            number_of_tasks_needing_knowledge = total_number_of_tasks[0]['ZahlAufgaben']
        else:
            number_of_tasks_needing_knowledge = 0
            text_to_print = "Dieser Wissensbaustein wird in dieser Lerneinheit nicht vermittelt. Oder haben Sie sich vielleicht vertippt?"
            return(text_to_print)
        
        if total_number_of_tasks != 0:

            number_of_tasks_needing_procedural_knowledge = 0
            number_of_tasks_needing_conceptual_knowledge = 0
            number_of_tasks_needing_factual_knowledge = 0
            number_of_tasks_needing_metacognitive_knowledge = 0

            if number_of_tasks_knowledge_dimensions:
                for record in number_of_tasks_knowledge_dimensions:
                    if record['Wissensdimension'] == 'needs_procedural_knowledge':
                        number_of_tasks_needing_procedural_knowledge=record['ZahlAufgaben']
                    elif record['Wissensdimension'] == 'needs_conceptual_knowledge':
                            number_of_tasks_needing_conceptual_knowledge=record['ZahlAufgaben']
                    elif record['Wissensdimension'] == 'needs_factual_knowledge':
                            number_of_tasks_needing_factual_knowledge=record['ZahlAufgaben']
                    elif record['Wissensdimension'] == 'needs_metacognitive_knowledge':
                            number_of_tasks_needing_metacognitive_knowledge=record['ZahlAufgaben']

            tasks_procedural=[]
            tasks_conceptual=[]
            tasks_factual=[]
            tasks_metacognitive=[]

            if tasks_knowledge_dimensions:
                for record in tasks_knowledge_dimensions:
                    if record['Wissensdimension'] == 'needs_procedural_knowledge':
                        tasks_procedural.append(record['Aufgabe'])
                    elif record['Wissensdimension'] == 'needs_conceptual_knowledge':
                            tasks_conceptual.append(record['Aufgabe'])
                    elif record['Wissensdimension'] == 'needs_factual_knowledge':
                            tasks_factual.append(record['Aufgabe'])
                    elif record['Wissensdimension'] == 'needs_metacognitive_knowledge':
                            tasks_metacognitive.append(record['Aufgabe'])


            text_to_print = "Der Wissensbaustein \"" + knowledge_name + "\" wird in insgesamt " + h_grammar_correction_task(number_of_tasks_needing_knowledge) + "vermittelt, davon in \n"
            if number_of_tasks_needing_procedural_knowledge!= 0:
                tasks_procedural.sort()
                text_to_print = text_to_print + "- " + h_grammar_correction_task(number_of_tasks_needing_procedural_knowledge) + "in der Dimension \"Prozedurales Wissen\" (" + (", ".join(tasks_procedural)) + ") \n"
            if number_of_tasks_needing_conceptual_knowledge!= 0:
                tasks_conceptual.sort()
                text_to_print = text_to_print + "- " + h_grammar_correction_task(number_of_tasks_needing_conceptual_knowledge) + "in der Dimension \"Konzeptuelles Wissen\" (" + (", ".join(tasks_conceptual)) + ") \n"
            if number_of_tasks_needing_factual_knowledge!= 0:
                tasks_factual.sort()
                text_to_print = text_to_print + "- " + h_grammar_correction_task(number_of_tasks_needing_factual_knowledge) + "in der Dimension \"Faktisches Wissen\" (" + (", ".join(tasks_factual)) + ") \n"
            if number_of_tasks_needing_metacognitive_knowledge!= 0:
                tasks_metacognitive.sort()
                text_to_print = text_to_print + "- " + h_grammar_correction_task(number_of_tasks_needing_metacognitive_knowledge) + "in der Dimension \"Metakognitives Wissen\" (" + (", ".join(tasks_metacognitive)) + ") \n"

            if number_of_tasks_needing_procedural_knowledge!= 0:
                text_to_print = text_to_print + "\nDetailinformationen zur Bearbeitung der Aufgaben, die " + knowledge_name + " in der Dimension \"Prozedurales Wissen\" vermitteln: \n"
                for task in tasks_procedural:
                    task_name = str(task)
                    number_of_students = h_get_number_of_students_covering_task(task_name)
                    number_of_students_doing_attempt = h_get_number_of_students_making_attempt_for_task(task_name)
                    number_of_attempts = h_get_number_of_attempts_for_task(task_name)
                    number_of_successful_attempts = h_get_number_of_successful_attempts_for_task(task_name)
                    average_time = h_get_average_time_spent_on_task(task_name)
                    total_time = h_get_total_time_spent_on_task(task_name)
                    total_time_print = h_change_minutes_to_hours(total_time)

                    text_to_print = text_to_print + " - Aufgabe \"" + str(task) + "\" wurde von " + h_grammar_correction_student_dat(number_of_students) + "bearbeitet und " + h_grammar_correction_student_nom(number_of_students_doing_attempt) + h_grammar_correction_haben(number_of_students_doing_attempt==1) + "mindestens einen Lösungsversuch unternommen. "
                    if number_of_attempts == 1:
                        text_to_print = text_to_print + "Der eine Lösungsversuch"
                        if number_of_successful_attempts==1:
                            text_to_print = text_to_print + " war erfolgreich (über 80 Prozent der Punkte erreicht). "
                        else: 
                            text_to_print = text_to_print + " war nicht erfolgreich (weniger als 80 Prozent der Punkte). "
                    elif number_of_attempts > 1:                  
                        text_to_print = text_to_print + "Von den insgesamt " + str(number_of_attempts) + " Lösungsversuchen" + h_grammar_correction_waren (number_of_successful_attempts==1) + str(number_of_successful_attempts) + " erfolgreich (mindestens 80 Prozent der Punkte). "
                    text_to_print = text_to_print + "Durchschnittlich wurden " + str(average_time) + " Minuten mit der Aufgabe verbracht und insgesamt " + total_time_print + ". \n"


            if number_of_tasks_needing_conceptual_knowledge!= 0:
                text_to_print = text_to_print + "\nDetailinformationen zur Bearbeitung der Aufgaben, die " + knowledge_name + " in der Dimension \"Konzeptuelles Wissen\" vermitteln: \n"
                for task in tasks_conceptual:
                    task_name = str(task)
                    number_of_students = h_get_number_of_students_covering_task(task_name)
                    number_of_students_doing_attempt = h_get_number_of_students_making_attempt_for_task(task_name)
                    number_of_attempts = h_get_number_of_attempts_for_task(task_name)
                    number_of_successful_attempts = h_get_number_of_successful_attempts_for_task(task_name)
                    average_time = h_get_average_time_spent_on_task(task_name)
                    total_time = h_get_total_time_spent_on_task(task_name)
                    total_time_print = h_change_minutes_to_hours(total_time)

                    text_to_print = text_to_print + " - Aufgabe \"" + str(task) + "\" wurde von " + h_grammar_correction_student_dat(number_of_students) + "bearbeitet und " + h_grammar_correction_student_nom(number_of_students_doing_attempt) + h_grammar_correction_haben(number_of_students_doing_attempt==1) + "mindestens einen Lösungsversuch unternommen. "
                    if number_of_attempts == 1:
                        text_to_print = text_to_print + "Der eine Lösungsversuch"
                        if number_of_successful_attempts==1:
                            text_to_print = text_to_print + " war erfolgreich (über 80 Prozent der Punkte erreicht). "
                        else: 
                            text_to_print = text_to_print + " war nicht erfolgreich (weniger als 80 Prozent der Punkte). "
                    elif number_of_attempts > 1:
                        text_to_print = text_to_print + "Von den insgesamt " + str(number_of_attempts) + " Lösungsversuchen" + h_grammar_correction_waren (number_of_successful_attempts==1) + str(number_of_successful_attempts) + " erfolgreich (mindestens 80 Prozent der Punkte). "
                    text_to_print = text_to_print + "Durchschnittlich wurden " + str(average_time) + " Minuten mit der Aufgabe verbracht und insgesamt " + total_time_print + ". \n"

            if number_of_tasks_needing_factual_knowledge!= 0:
                text_to_print = text_to_print + "\nDetailinformationen zur Bearbeitung der Aufgaben, die " + knowledge_name + " in der Dimension \"Faktisches Wissen\" vermitteln: \n"
                for task in tasks_factual:
                    task_name = str(task)
                    number_of_students = h_get_number_of_students_covering_task(task_name)
                    number_of_students_doing_attempt = h_get_number_of_students_making_attempt_for_task(task_name)
                    number_of_attempts = h_get_number_of_attempts_for_task(task_name)
                    number_of_successful_attempts = h_get_number_of_successful_attempts_for_task(task_name)
                    average_time = h_get_average_time_spent_on_task(task_name)
                    total_time = h_get_total_time_spent_on_task(task_name)
                    total_time_print = h_change_minutes_to_hours(total_time)

                    text_to_print = text_to_print + " - Aufgabe \"" + str(task) + "\" wurde von " + h_grammar_correction_student_dat(number_of_students) + "bearbeitet und " + h_grammar_correction_student_nom(number_of_students_doing_attempt) + h_grammar_correction_haben(number_of_students_doing_attempt==1) + "mindestens einen Lösungsversuch unternommen. "
                    if number_of_attempts == 1:
                        text_to_print = text_to_print + "Der eine Lösungsversuch"
                        if number_of_successful_attempts==1:
                            text_to_print = text_to_print + " war erfolgreich (über 80 Prozent der Punkte erreicht). "
                        else: 
                            text_to_print = text_to_print + " war nicht erfolgreich (weniger als 80 Prozent der Punkte). "
                    elif number_of_attempts > 1:
                        text_to_print = text_to_print + "Von den insgesamt " + str(number_of_attempts) + " Lösungsversuchen" + h_grammar_correction_waren (number_of_successful_attempts==1) + str(number_of_successful_attempts) + " erfolgreich (mindestens 80 Prozent der Punkte). "
                    text_to_print = text_to_print + "Durchschnittlich wurden " + str(average_time) + " Minuten mit der Aufgabe verbracht und insgesamt " + total_time_print + ". \n"


            if number_of_tasks_needing_metacognitive_knowledge!= 0:
                text_to_print = text_to_print + "\nDetailinformationen zur Bearbeitung der Aufgaben, die " + knowledge_name + " in der Dimension \"Metakognitives Wissen\" vermitteln: \n"
                for task in tasks_procedural:
                    task_name = str(task)
                    number_of_students = h_get_number_of_students_covering_task(task_name)
                    number_of_students_doing_attempt = h_get_number_of_students_making_attempt_for_task(task_name)
                    number_of_attempts = h_get_number_of_attempts_for_task(task_name)
                    number_of_successful_attempts = h_get_number_of_successful_attempts_for_task(task_name)
                    average_time = h_get_average_time_spent_on_task(task_name)
                    total_time = h_get_total_time_spent_on_task(task_name)
                    total_time_print = h_change_minutes_to_hours(total_time)

                    text_to_print = text_to_print + " - Aufgabe \"" + str(task) + "\" wurde von " + h_grammar_correction_student_dat(number_of_students) + "bearbeitet und " + h_grammar_correction_student_nom(number_of_students_doing_attempt) + h_grammar_correction_haben(number_of_students_doing_attempt==1) + "mindestens einen Lösungsversuch unternommen. "
                    if number_of_attempts == 1:
                        text_to_print = text_to_print + "Der eine Lösungsversuch"
                        if number_of_successful_attempts==1:
                            text_to_print = text_to_print + " war erfolgreich (über 80 Prozent der Punkte erreicht). "
                        else: 
                            text_to_print = text_to_print + " war nicht erfolgreich (weniger als 80 Prozent der Punkte). "
                    elif number_of_attempts > 1:
                        text_to_print = text_to_print + "Von den insgesamt " + str(number_of_attempts) + " Lösungsversuchen" + h_grammar_correction_waren (number_of_successful_attempts==1) + str(number_of_successful_attempts) + " erfolgreich (mindestens 80 Prozent der Punkte). "
                    text_to_print = text_to_print + "Durchschnittlich wurden " + str(average_time) + " Minuten mit der Aufgabe verbracht und insgesamt " + total_time_print + ". \n"

    except Neo4jError as e:
        text_to_print = "Es ist ein Fehler beim Einholen von Informationen über das Wissenselement \"" + knowledge_name + "\" aufgetreten."
        text_to_print = text_to_print + "Neo4j error code: " + str(e.code) + "; "
        if e.message is not None:
            text_to_print = text_to_print + "Exception message: " + e.message
    
    return text_to_print

# gibt Informationen (Text) darüber zurück, in wie vielen und welchen Aufgaben eine Fähigkeit vermittelt wird und wie viele Studierenden diese Aufgaben mit welchem Erfolg bearbeitet haben
def h_get_information_on_skill(skill_id):
    skill_name = h_get_skill_name_for_id(skill_id)
    if skill_name == "":
        # Fehlermeldung schon in Funktion ausgegeben
        return

    try:
        with driver.session() as session:   
            params = {"skill_id" : skill_id}
            total_number_of_tasks = session.run("""
                MATCH (sk:Skill {sk_ID: $skill_id})<-[r]-(lt:Learning_Task)
                RETURN COUNT(DISTINCT lt) AS ZahlAufgaben""", params).data()
            number_of_tasks_taxonomy_levels = session.run("""
                MATCH (sk:Skill {sk_ID: $skill_id})<-[r]-(lt:Learning_Task)
                RETURN type(r) AS Taxonomiestufe, COUNT(DISTINCT lt) AS ZahlAufgaben""", params).data()
            tasks_taxonomy_levels = session.run("""
                MATCH (sk:Skill {sk_ID: $skill_id})<-[r]-(lt:Learning_Task)
                RETURN type(r) AS Taxonomiestufe, lt.title AS Aufgabe""", params).data()
            
            if total_number_of_tasks and tasks_taxonomy_levels and total_number_of_tasks[0]['ZahlAufgaben'] is not None:
                number_of_tasks_involving_skill = total_number_of_tasks[0]['ZahlAufgaben']
                
                if number_of_tasks_involving_skill == 0:
                    return "Keine der Aufgaben im Kurs erfordert diese Fähigkeit."

                number_of_tasks_involving_skill_remember = 0
                number_of_tasks_involving_skill_understand = 0
                number_of_tasks_involving_skill_apply = 0
                number_of_tasks_involving_skill_analyze = 0
                number_of_tasks_involving_skill_evaluate = 0
                number_of_tasks_involving_skill_create = 0
                
                
                for record in number_of_tasks_taxonomy_levels:
                        if record['Taxonomiestufe'] == 'remembers':
                            number_of_tasks_involving_skill_remember=record['ZahlAufgaben']
                        elif record['Taxonomiestufe'] == 'understands':
                            number_of_tasks_involving_skill_understand=record['ZahlAufgaben']
                        elif record['Taxonomiestufe'] == 'applies':
                            number_of_tasks_involving_skill_apply=record['ZahlAufgaben']
                        elif record['Taxonomiestufe'] == 'analyzes':
                            number_of_tasks_involving_skill_analyze=record['ZahlAufgaben']
                        elif record['Taxonomiestufe'] == 'evaluates':
                            number_of_tasks_involving_skill_evaluate=record['ZahlAufgaben']
                        elif record['Taxonomiestufe'] == 'creates':
                                number_of_tasks_involving_skill_create=record['ZahlAufgaben']

                remember_list=[]
                understand_list=[]
                apply_list=[]
                analyze_list=[]
                evaluate_list=[]
                create_list=[]

                for record in tasks_taxonomy_levels:
                    if record['Taxonomiestufe'] == 'remembers':
                        remember_list.append(record['Aufgabe'])
                    elif record['Taxonomiestufe'] == 'understands':
                        understand_list.append(record['Aufgabe'])
                    elif record['Taxonomiestufe'] == 'applies':
                        apply_list.append(record['Aufgabe'])
                    elif record['Taxonomiestufe'] == 'analyzes':
                        analyze_list.append(record['Aufgabe'])
                    elif record['Taxonomiestufe'] == 'evaluates':
                        evaluate_list.append(record['Aufgabe'])
                    elif record['Taxonomiestufe'] == 'creates':
                        create_list.append(record['Aufgabe'])

                remember_list.sort()
                understand_list.sort()
                apply_list.sort()
                analyze_list.sort()
                evaluate_list.sort()
                create_list.sort()

                text_to_print = "Die Fähigkeit \"" + skill_name + "\" wird in insgesamt " + h_grammar_correction_task(number_of_tasks_involving_skill) + "vermittelt, davon in \n"
                if number_of_tasks_involving_skill_remember!=0:
                    text_to_print = text_to_print + "- " + h_grammar_correction_task(number_of_tasks_involving_skill_remember) + "auf der Taxonomiestufe \"Erinnern\" (" + (", ".join(remember_list)) + ") \n"
                if number_of_tasks_involving_skill_understand!=0:
                    text_to_print = text_to_print + "- " + h_grammar_correction_task(number_of_tasks_involving_skill_understand) + "auf der Taxonomiestufe \"Verstehen\" (" + (", ".join(understand_list)) + ") \n"
                if number_of_tasks_involving_skill_apply!=0:
                    text_to_print = text_to_print + "- " + h_grammar_correction_task(number_of_tasks_involving_skill_apply) + "auf der Taxonomiestufe \"Anwenden\" (" + (", ".join(apply_list)) + ") \n"
                if number_of_tasks_involving_skill_analyze!=0:
                    text_to_print = text_to_print + "- " + h_grammar_correction_task(number_of_tasks_involving_skill_analyze) + "auf der Taxonomiestufe \"Analysieren\" (" + (", ".join(analyze_list)) + ") \n"
                if number_of_tasks_involving_skill_evaluate!=0:
                    text_to_print = text_to_print + "- " + h_grammar_correction_task(number_of_tasks_involving_skill_evaluate) + "auf der Taxonomiestufe \"Bewerten\" (" + (", ".join(evaluate_list)) + ") \n"
                if number_of_tasks_involving_skill_create!=0:
                    text_to_print = text_to_print + "- " + h_grammar_correction_task(number_of_tasks_involving_skill_create) + "auf der Taxonomiestufe \"Erstellen\" (" + (", ".join(create_list)) + ") \n"


                if number_of_tasks_involving_skill_remember:
                    text_to_print = text_to_print + "\nDetailinformationen zur Bearbeitung der Aufgaben, die \"" + skill_name + "\" auf der Taxonomiestufe \"Erinnern\" vermitteln: \n"     
                    for task in remember_list:
                        task_name = str(task)
                        number_of_students = h_get_number_of_students_covering_task(task_name)
                        number_of_students_doing_attempt = h_get_number_of_students_making_attempt_for_task(task_name)
                        number_of_attempts = h_get_number_of_attempts_for_task(task_name)
                        number_of_successful_attempts = h_get_number_of_successful_attempts_for_task(task_name)
                        average_time = h_get_average_time_spent_on_task(task_name)
                        total_time = h_get_total_time_spent_on_task(task_name)
                        total_time_print = h_change_minutes_to_hours(total_time)
                        text_to_print = text_to_print + " - Aufgabe \"" + str(task) + "\" wurde von " + h_grammar_correction_student_dat(number_of_students) + "bearbeitet und " + h_grammar_correction_student_nom(number_of_students_doing_attempt) + h_grammar_correction_haben(number_of_students_doing_attempt==1) + "mindestens einen Lösungsversuch unternommen. "
                        if number_of_attempts == 1:
                            text_to_print = text_to_print + "Der eine Lösungsversuch"
                            if number_of_successful_attempts==1:
                                text_to_print = text_to_print + " war erfolgreich (über 80 Prozent der Punkte erreicht). "
                            else: 
                                text_to_print = text_to_print + " war nicht erfolgreich (weniger als 80 Prozent der Punkte). "
                        elif number_of_attempts > 1:
                            text_to_print = text_to_print + "Von den insgesamt " + str(number_of_attempts) + " Lösungsversuchen" + h_grammar_correction_waren (number_of_successful_attempts==1) + str(number_of_successful_attempts) + " erfolgreich (mindestens 80 Prozent der Punkte). "
                        text_to_print = text_to_print + "Durchschnittlich wurden " + str(average_time) + " Minuten mit der Aufgabe verbracht und insgesamt " + total_time_print + ". \n"

                if number_of_tasks_involving_skill_understand:
                    text_to_print = text_to_print + "\nDetailinformationen zur Bearbeitung der Aufgaben, die \"" + skill_name + "\" auf der Taxonomiestufe \"Verstehen\" vermitteln: \n"     
                    for task in understand_list:
                        task_name = str(task)
                        number_of_students = h_get_number_of_students_covering_task(task_name)
                        number_of_students_doing_attempt = h_get_number_of_students_making_attempt_for_task(task_name)
                        number_of_attempts = h_get_number_of_attempts_for_task(task_name)
                        number_of_successful_attempts = h_get_number_of_successful_attempts_for_task(task_name)
                        average_time = h_get_average_time_spent_on_task(task_name)
                        total_time = h_get_total_time_spent_on_task(task_name)
                        total_time_print = h_change_minutes_to_hours(total_time)

                        text_to_print = text_to_print + " - Aufgabe \"" + str(task) + "\" wurde von " + h_grammar_correction_student_dat(number_of_students) + "bearbeitet und " + h_grammar_correction_student_nom(number_of_students_doing_attempt) + h_grammar_correction_haben(number_of_students_doing_attempt==1) + "mindestens einen Lösungsversuch unternommen. "
                        if number_of_attempts == 1:
                            text_to_print = text_to_print + "Der eine Lösungsversuch"
                            if number_of_successful_attempts==1:
                                text_to_print = text_to_print + " war erfolgreich (über 80 Prozent der Punkte erreicht). "
                            else: 
                                text_to_print = text_to_print + " war nicht erfolgreich (weniger als 80 Prozent der Punkte). "
                        elif number_of_attempts > 1:
                            text_to_print = text_to_print + "Von den insgesamt " + str(number_of_attempts) + " Lösungsversuchen" + h_grammar_correction_waren (number_of_successful_attempts==1) + str(number_of_successful_attempts) + " erfolgreich (mindestens 80 Prozent der Punkte). "
                        text_to_print = text_to_print + "Durchschnittlich wurden " + str(average_time) + " Minuten mit der Aufgabe verbracht und insgesamt " + total_time_print + ". \n"

                if number_of_tasks_involving_skill_apply:
                    text_to_print = text_to_print + "\nDetailinformationen zur Bearbeitung der Aufgaben, die \"" + skill_name + "\" auf der Taxonomiestufe \"Anwenden\" vermitteln: \n"     
                    for task in apply_list:
                        task_name = str(task)
                        number_of_students = h_get_number_of_students_covering_task(task_name)
                        number_of_students_doing_attempt = h_get_number_of_students_making_attempt_for_task(task_name)
                        number_of_attempts = h_get_number_of_attempts_for_task(task_name)
                        number_of_successful_attempts = h_get_number_of_successful_attempts_for_task(task_name)
                        average_time = h_get_average_time_spent_on_task(task_name)
                        total_time = h_get_total_time_spent_on_task(task_name)
                        total_time_print = h_change_minutes_to_hours(total_time)

                        text_to_print = text_to_print + " - Aufgabe \"" + str(task) + "\" wurde von " + h_grammar_correction_student_dat(number_of_students) + "bearbeitet und " + h_grammar_correction_student_nom(number_of_students_doing_attempt) + h_grammar_correction_haben(number_of_students_doing_attempt==1) + "mindestens einen Lösungsversuch unternommen. "
                        if number_of_attempts == 1:
                            text_to_print = text_to_print + "Der eine Lösungsversuch"
                            if number_of_successful_attempts==1:
                                text_to_print = text_to_print + " war erfolgreich (über 80 Prozent der Punkte erreicht). "
                            else: 
                                text_to_print = text_to_print + " war nicht erfolgreich (weniger als 80 Prozent der Punkte). "
                        elif number_of_attempts > 1:
                            text_to_print = text_to_print + "Von den insgesamt " + str(number_of_attempts) + " Lösungsversuchen" + h_grammar_correction_waren (number_of_successful_attempts==1) + str(number_of_successful_attempts) + " erfolgreich (mindestens 80 Prozent der Punkte). "
                        text_to_print = text_to_print + "Durchschnittlich wurden " + str(average_time) + " Minuten mit der Aufgabe verbracht und insgesamt " + total_time_print + ". \n"

                if number_of_tasks_involving_skill_analyze:
                    text_to_print = text_to_print + "\nDetailinformationen zur Bearbeitung der Aufgaben, die \"" + skill_name + "\" auf der Taxonomiestufe \"Analysieren\" vermitteln: \n"     
                    for task in analyze_list:
                        task_name = str(task)
                        number_of_students = h_get_number_of_students_covering_task(task_name)
                        number_of_students_doing_attempt = h_get_number_of_students_making_attempt_for_task(task_name)
                        number_of_attempts = h_get_number_of_attempts_for_task(task_name)
                        number_of_successful_attempts = h_get_number_of_successful_attempts_for_task(task_name)
                        average_time = h_get_average_time_spent_on_task(task_name)
                        total_time = h_get_total_time_spent_on_task(task_name)
                        total_time_print = h_change_minutes_to_hours(total_time)

                        text_to_print = text_to_print + " - Aufgabe \"" + str(task) + "\" wurde von " + h_grammar_correction_student_dat(number_of_students) + "bearbeitet und " + h_grammar_correction_student_nom(number_of_students_doing_attempt) + h_grammar_correction_haben(number_of_students_doing_attempt==1) + "mindestens einen Lösungsversuch unternommen. "
                        if number_of_attempts == 1:
                            text_to_print = text_to_print + "Der eine Lösungsversuch"
                            if number_of_successful_attempts==1:
                                text_to_print = text_to_print + " war erfolgreich (über 80 Prozent der Punkte erreicht). "
                            else: 
                                text_to_print = text_to_print + " war nicht erfolgreich (weniger als 80 Prozent der Punkte). "
                        elif number_of_attempts > 1:
                            text_to_print = text_to_print + "Von den insgesamt " + str(number_of_attempts) + " Lösungsversuchen" + h_grammar_correction_waren (number_of_successful_attempts==1) + str(number_of_successful_attempts) + " erfolgreich (mindestens 80 Prozent der Punkte). "
                        text_to_print = text_to_print + "Durchschnittlich wurden " + str(average_time) + " Minuten mit der Aufgabe verbracht und insgesamt " + total_time_print + ". \n"

                if number_of_tasks_involving_skill_evaluate:
                    text_to_print = text_to_print + "\nDetailinformationen zur Bearbeitung der Aufgaben, die \"" + skill_name + "\" auf der Taxonomiestufe \"Bewerten\" vermitteln: \n"     
                    for task in evaluate_list:
                        task_name = str(task)
                        number_of_students = h_get_number_of_students_covering_task(task_name)
                        number_of_students_doing_attempt = h_get_number_of_students_making_attempt_for_task(task_name)
                        number_of_attempts = h_get_number_of_attempts_for_task(task_name)
                        number_of_successful_attempts = h_get_number_of_successful_attempts_for_task(task_name)
                        average_time = h_get_average_time_spent_on_task(task_name)
                        total_time = h_get_total_time_spent_on_task(task_name)
                        total_time_print = h_change_minutes_to_hours(total_time)

                        text_to_print = text_to_print + " - Aufgabe \"" + str(task) + "\" wurde von " + h_grammar_correction_student_dat(number_of_students) + "bearbeitet und " + h_grammar_correction_student_nom(number_of_students_doing_attempt) + h_grammar_correction_haben(number_of_students_doing_attempt==1) + "mindestens einen Lösungsversuch unternommen. "
                        if number_of_attempts == 1:
                            text_to_print = text_to_print + "Der eine Lösungsversuch"
                            if number_of_successful_attempts==1:
                                text_to_print = text_to_print + " war erfolgreich (über 80 Prozent der Punkte erreicht). "
                            else: 
                                text_to_print = text_to_print + " war nicht erfolgreich (weniger als 80 Prozent der Punkte). "
                        elif number_of_attempts > 1:
                            text_to_print = text_to_print + "Von den insgesamt " + str(number_of_attempts) + " Lösungsversuchen" + h_grammar_correction_waren (number_of_successful_attempts==1) + str(number_of_successful_attempts) + " erfolgreich (mindestens 80 Prozent der Punkte). "
                        text_to_print = text_to_print + "Durchschnittlich wurden " + str(average_time) + " Minuten mit der Aufgabe verbracht und insgesamt " + total_time_print + ". \n"

                if number_of_tasks_involving_skill_create:
                    text_to_print = text_to_print + "\nDetailinformationen zur Bearbeitung der Aufgaben, die \"" + skill_name + "\" auf der Taxonomiestufe \"Erstellen\" vermitteln: \n"     
                    for task in create_list:
                        task_name = str(task)
                        number_of_students = h_get_number_of_students_covering_task(task_name)
                        number_of_students_doing_attempt = h_get_number_of_students_making_attempt_for_task(task_name)
                        number_of_attempts = h_get_number_of_attempts_for_task(task_name)
                        number_of_successful_attempts = h_get_number_of_successful_attempts_for_task(task_name)
                        average_time = h_get_average_time_spent_on_task(task_name)
                        total_time = h_get_total_time_spent_on_task(task_name)
                        total_time_print = h_change_minutes_to_hours(total_time)

                        text_to_print = text_to_print + " - Aufgabe \"" + str(task) + "\" wurde von " + h_grammar_correction_student_dat(number_of_students) + "bearbeitet und " + h_grammar_correction_student_nom(number_of_students_doing_attempt) + h_grammar_correction_haben(number_of_students_doing_attempt==1) + "mindestens einen Lösungsversuch unternommen. "
                        if number_of_attempts == 1:
                            text_to_print = text_to_print + "Der eine Lösungsversuch"
                            if number_of_successful_attempts==1:
                                text_to_print = text_to_print + " war erfolgreich (über 80 Prozent der Punkte erreicht). "
                            else: 
                                text_to_print = text_to_print + " war nicht erfolgreich (weniger als 80 Prozent der Punkte). "
                        elif number_of_attempts > 1:
                            text_to_print = text_to_print + "Von den insgesamt " + str(number_of_attempts) + " Lösungsversuchen" + h_grammar_correction_waren (number_of_successful_attempts==1) + str(number_of_successful_attempts) + " erfolgreich (mindestens 80 Prozent der Punkte). "
                        text_to_print = text_to_print + "Durchschnittlich wurden " + str(average_time) + " Minuten mit der Aufgabe verbracht und insgesamt " + total_time_print + ". \n"


            else:
                return "Keine der Aufgaben im Kurs erfordert diese Fähigkeit."


    except Neo4jError as e:
        text_to_print = "Es ist ein Fehler beim Einholen von Informationen über die Fähigkeit \"" + skill_name + "\" aufgetreten."
        text_to_print = "Neo4j error code: " + str(e.code) + "; "
        if e.message is not None:
            text_to_print = text_to_print + "Exception message: " + e.message
    
    return text_to_print

#### eigentliche Ausgabefunktionen
## Info zu Student
# gibt allgemeine Informationen zum Lernverhalten des Studierenden aus (Zeit im Kurs, erzielte Punkte ...) darunter auch schon den Inhalt der Funktion print_information_on_difficult_tasks_for_student aus
def print_general_information_on_student(last_name):
    if h_test_if_student(last_name)==False:
        print("Scheinbar gibt es keinen Nutzer mit diesem Namen. Haben Sie sich vielleicht vertippt?")
        return

    try:
        with driver.session() as session:
            params = {"last_name" : last_name}
            time_in_course = session.run("""
                MATCH(s:Student {last_name: $last_name})-[r:did_learning_session]-(ls:Learning_Session)
                WITH duration.between(datetime(ls.start_time), datetime(ls.end_time)) AS Minuten
                RETURN sum(Minuten) AS Gesamtzeit""", params).data()
            number_of_sessions = session.run("""
                MATCH(s:Student {last_name: $last_name})-[r:did_learning_session]-(ls:Learning_Session)
                RETURN count(ls) AS AnzahlLernsitzungen""", params).data()
            start_time = session.run("""
                MATCH(s:Student {last_name: $last_name})-[r:did_learning_session]-(ls:Learning_Session)
                RETURN ls.start_time as Startzeit ORDER BY Startzeit LIMIT 1""", params).data()
            end_time = session.run("""
                MATCH(s:Student {last_name: $last_name})-[r:did_learning_session]-(ls:Learning_Session)
                RETURN ls.end_time as Endzeit ORDER BY Endzeit DESC LIMIT 1""", params).data()
            number_of_completed_tasks = session.run("""
                MATCH(s:Student {last_name: $last_name})-[c:completed]->(lt:Learning_Task)
                RETURN count(lt) AS AnzahlAbgeschlosseneÜbungen""", params).data()
            number_of_reached_points = session.run("""
                MATCH(s:Student {last_name: $last_name})-[c:completed]->(lt:Learning_Task)
                WHERE c.type = "attempt"
                RETURN SUM(c.score) AS ErreichtePunktzahl""", params).data()
            number_of_completed_si = session.run("""
                MATCH(s:Student {last_name: $last_name})-[c:completed]-(si:Supportive_Information)
                RETURN COUNT(si) AS AnzahlAbgeschlosseneSI""", params).data()            
            number_of_completed_pi = session.run("""
                MATCH(s:Student {last_name: $last_name})-[c:completed]-(pi:Procedural_Information)
                RETURN COUNT(pi) AS AnzahlAbgeschlossenePI""", params).data()
            pages_not_visited = session.run("""
                MATCH(im:Information_Material)
                WHERE NOT EXISTS {(s:Student {last_name: $last_name})-[]->(ls:Learning_Session)-[:covered]-(im)}
                RETURN im.title AS Aufgabe""", params).data() 
            full_points_first_try = session.run("""
                MATCH(s:Student {last_name: $last_name})-[r:successfully_solved|struggled_with]->(lt:Learning_Task)
                WITH s, r, lt
                ORDER BY lt.title, r.timestamp
                WITH s, lt, COLLECT(r)[0] AS ErsterVersuch
                WHERE ErsterVersuch.score = 10
                RETURN lt.title AS Aufgabe, ErsterVersuch.timestamp""", params).data()
            most_time_spent_on_task = session.run("""
                MATCH (s:Student {last_name: $last_name})-[]->(ls:Learning_Session)-[c:covered]->(lt:Learning_Task)
                RETURN lt.title AS Aufgabe, SUM(c.time_spent) AS VerbrachteZeit ORDER BY VerbrachteZeit DESC LIMIT 1""", params).data() 
            average_time_spent_on_task = session.run("""
                MATCH (s:Student {last_name: $last_name})-[]->(ls:Learning_Session)-[c:covered]->(lt:Learning_Task)
                WITH lt.title AS Aufgabe, SUM(c.time_spent) AS DauerProAufgabe
                RETURN AVG(DauerProAufgabe) AS DurchschnittlichVerbrachteZeit""", params).data() 
            total_time_spent_on_tasks = session.run("""
                MATCH(s:Student {last_name: $last_name})-[d:did_learning_session]->(ls:Learning_Session)-[c:covered]->(lt:Learning_Task)
                RETURN SUM(c.time_spent) As GesamtzeitAufgabe""", params).data() 
            most_time_spent_on_information_material = session.run("""
                MATCH (s:Student {last_name: $last_name})-[]->(ls:Learning_Session)-[c:covered]->(im:Information_Material) 
                RETURN im.title AS Aufgabe, SUM(c.time_spent) AS VerbrachteZeit ORDER BY VerbrachteZeit DESC LIMIT 1""", params).data() 
            average_time_spent_on_information_material = session.run("""
                MATCH (s:Student {last_name: $last_name})-[]->(ls:Learning_Session)-[c:covered]->(im:Information_Material)
                WITH im.title AS InfoMat, SUM(c.time_spent) AS DauerProSeite
                RETURN AVG(DauerProSeite) AS DurchschnittlichVerbrachteZeit""", params).data() 
            total_time_spent_on_information_material = session.run("""
                MATCH(s:Student {last_name: $last_name})-[d:did_learning_session]->(ls:Learning_Session)-[c:covered]->(im: Information_Material)
                RETURN SUM(c.time_spent) AS GesamtzeitInfoMat""", params).data() 
            cypher_for_sessions_plot = session.run(""" 
                MATCH(s: Student {last_name: $last_name})-[d]->(ls:Learning_Session)
                RETURN ls.start_time AS Startzeit, ls.end_time AS Endzeit, duration.between(ls.start_time, ls.end_time).MINUTES AS Dauer""", params)
            data_for_sessions_plot = [record.data() for record in cypher_for_sessions_plot]
            cypher_for_results_plot = session.run("""
                MATCH(s:Student {last_name: $last_name})-[c:completed]-(ls:Learning_Task)
                RETURN ls.title AS Aufgabe, c.score AS Punktzahl""", params)
            data_for_results_plot = [record.data() for record in cypher_for_results_plot]
                   
        text_to_print = ""
        error_text = ""

        if start_time and end_time and number_of_sessions and time_in_course and start_time[0]['Startzeit'] is not None and end_time[0]['Endzeit'] is not None and number_of_sessions[0]['AnzahlLernsitzungen'] is not None and time_in_course[0]['Gesamtzeit'] is not None:
            startzeit = start_time[0]['Startzeit'].strftime('%Y-%m-%d %H:%M')
            endzeit = end_time[0]['Endzeit'].strftime('%Y-%m-%d %H:%M')
            number_of_learning_sessions = number_of_sessions[0]['AnzahlLernsitzungen']
            total_time_spent_in_course = h_normalize_duration(time_in_course[0]['Gesamtzeit'])
            text_to_print = text_to_print + "Der Studierende hat den Kurs im Zeitraum von " + str(startzeit) + " bis " + str(endzeit) + " in " + str(number_of_learning_sessions) + " Lernsitzungen insgesamt" + total_time_spent_in_course + "bearbeitet.\n"
        else:
            error_text = error_text + "Es ist ein Fehler bei der Berechnung der ersten oder letzten Lernsitzung, der Anzahl der Lernsitzungen oder der im Kurs verbrachten Zeit aufgetreten. "

        if data_for_sessions_plot!=[]:
            learning_sessions = pd.DataFrame(data_for_sessions_plot)
        else:
            learning_sessions = pd.DataFrame()
        
        if not learning_sessions.empty:
            learning_sessions['Startzeit'] = learning_sessions['Startzeit'].apply(lambda x: x.to_native() if hasattr(x, 'to_native') else x)
            learning_sessions['Endzeit'] = learning_sessions['Endzeit'].apply(lambda x: x.to_native() if hasattr(x, 'to_native') else x)
            learning_sessions['Startzeit'] = pd.to_datetime(learning_sessions['Startzeit'])
            learning_sessions['Endzeit'] = pd.to_datetime(learning_sessions['Endzeit']) 

            learning_sessions['Woche'] = learning_sessions['Startzeit'].dt.to_period('W')
            weekly_data = learning_sessions.groupby('Woche')['Dauer'].sum().reset_index()
            weekly_data['Woche'] = weekly_data['Woche'].astype(str)
            
            plt.figure(figsize=(10, 6))
            sns.barplot(x='Woche', y='Dauer', data=weekly_data, color='#2cb794')
            plt.title('Zeit im Kurs pro Woche')
            plt.xlabel('Woche')
            plt.ylabel('Gesamtzeit (Minuten)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig('output/learning_time_total.png')
            plt.clf()
            print('Eine Darstellung der Verteilung der Lernzeit auf die Kurswochen ist zu finden unter graph-container/shared_data/images/learning_time_total.png')

        if data_for_results_plot!=[]:
            results_for_plot = pd.DataFrame(data_for_results_plot)
            results_for_plot['Aufgabe'] = results_for_plot['Aufgabe'].str[:2]
        else:
            results_for_plot = pd.DataFrame()

        if not results_for_plot.empty:     
            plt.figure(figsize=(10, 6))
            sns.barplot(x='Aufgabe', y='Punktzahl', data=results_for_plot, color='#2cb794')
            plt.title('Ergebnisse bei den Aufgaben')
            plt.xlabel('Aufgabe')
            plt.ylabel('Erzielte Punkte')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig('output/student_results.png')
            print('Eine Darstellung der Ergebnisse des Studierenden bei den einzelnen Aufgaben ist zu finden unter graph-container/shared_data/images/student_results.png')
            plt.clf()
            plt.close()


        if number_of_completed_tasks and number_of_reached_points and number_of_completed_tasks[0]['AnzahlAbgeschlosseneÜbungen'] is not None and number_of_reached_points[0]['ErreichtePunktzahl'] is not None:
            number_of_tasks_in_course = h_get_number_of_learning_tasks()
            number_of_completed_tasks = number_of_completed_tasks[0]['AnzahlAbgeschlosseneÜbungen']
            percentage_of_completed_tasks = round(number_of_completed_tasks/number_of_tasks_in_course*100)
            number_of_reached_points = round(number_of_reached_points[0]['ErreichtePunktzahl'])
            number_of_attainable_points = number_of_completed_tasks*10
            text_to_print = text_to_print + "Er/Sie hat dabei " + str(percentage_of_completed_tasks) + " Prozent der Aufgaben mit insgesamt rund " + str(number_of_reached_points) + " von den in diesen Aufgaben erreichbaren " + str(number_of_attainable_points) + " Punkten und von den insgesamt erreichbaren " + str(number_of_tasks_in_course*10) + " Punkten abgeschlossen. "
        else:
            error_text = error_text + "Es ist ein Fehler bei der Berechnung der vom Studierenden abgeschlossenen Übungen oder der erreichten Punkte aufgetreten. "

        if number_of_completed_si and number_of_completed_pi and number_of_completed_si[0]['AnzahlAbgeschlosseneSI'] is not None and number_of_completed_pi[0]['AnzahlAbgeschlossenePI'] is not None:
            number_of_si_in_course = h_get_number_of_si()
            number_of_completed_si = number_of_completed_si[0]['AnzahlAbgeschlosseneSI']
            percentage_of_completed_si = round(number_of_completed_si/number_of_si_in_course*100)
            number_of_pi_in_course = h_get_number_of_pi()
            number_of_completed_pi = number_of_completed_pi[0]['AnzahlAbgeschlossenePI']
            percentage_of_completed_pi = round(number_of_completed_pi/number_of_pi_in_course*100)
            text_to_print = text_to_print + str(percentage_of_completed_si) + " Prozent der Supportive Information und " + str(percentage_of_completed_pi) + " Prozent der Procedural Information wurden als abgeschlossen markiert. "
        else:
            error_text = error_text + "Es ist ein Fehler bei der Berechnung der vom Studierenden abgeschlossenen Procedural oder Supportive Information-Elemente aufgetreten. "

        if pages_not_visited:
            pages_not_visited_list = [record['Aufgabe'] for record in pages_not_visited]
            text_to_print = text_to_print + "Die Seiten " + (", ".join(pages_not_visited_list)) + " wurden gar nicht besucht. "

        if full_points_first_try and full_points_first_try[0]['Aufgabe'] is not None:
            full_points_task_list = []
            for record in full_points_first_try:
                full_points_task_list.append(record['Aufgabe'])
            text_to_print = text_to_print + "Bei den Übungen " + (", ".join(full_points_task_list)) + " hat der Studierende direkt im ersten Versuch die volle Punktzahl erzielt."

        print(text_to_print)

        print_information_on_difficult_tasks_for_student(last_name)
        text_to_print = "\n"
        
        if most_time_spent_on_task and most_time_spent_on_task[0]['Aufgabe'] is not None:
            most_time_spent_on_task_title = most_time_spent_on_task[0]['Aufgabe']
            most_time_spent_on_task_time = h_change_minutes_to_hours(round(most_time_spent_on_task[0]['VerbrachteZeit']))
            text_to_print = text_to_print + "In Bezug auf die Aufgaben hat der Studierende die meiste Zeit mit Aufgabe " + str(most_time_spent_on_task_title) + " (" + most_time_spent_on_task_time + ") verbracht. "

        if most_time_spent_on_information_material and most_time_spent_on_information_material[0]['Aufgabe'] is not None:
            most_time_spent_on_information_material_title = most_time_spent_on_information_material[0]['Aufgabe']
            most_time_spent_on_information_material_time = h_change_minutes_to_hours(round(most_time_spent_on_information_material[0]['VerbrachteZeit']))
            text_to_print = text_to_print + "Was Informationsmaterial angeht, so hat der Studierende die meiste Zeit mit " + str(most_time_spent_on_information_material_title) + " (" + most_time_spent_on_information_material_time + ") verbracht. "


        if average_time_spent_on_task and average_time_spent_on_task[0]['DurchschnittlichVerbrachteZeit'] is not None and total_time_spent_on_tasks and total_time_spent_on_tasks[0]['GesamtzeitAufgabe'] is not None:
            average_time_spent_on_task_time = h_change_minutes_to_hours(round(average_time_spent_on_task[0]['DurchschnittlichVerbrachteZeit']))
            total_time_spent_on_tasks_time = h_change_minutes_to_hours(round(total_time_spent_on_tasks[0]['GesamtzeitAufgabe']))
            text_to_print = text_to_print + "Im Durchschnitt hat der Studierende\n - " + average_time_spent_on_task_time + " mit Aufgaben (insgesamt " + total_time_spent_on_tasks_time + " )"
        else:
            text_to_print = text_to_print + "Im Durchschnitt hat der Studierende\n - 0 Minuten mit Aufgaben "
        
        if average_time_spent_on_information_material and average_time_spent_on_information_material[0]['DurchschnittlichVerbrachteZeit'] is not None and total_time_spent_on_information_material and total_time_spent_on_information_material[0]['GesamtzeitInfoMat'] is not None:
            average_time_spent_on_information_material_time = h_change_minutes_to_hours(round(average_time_spent_on_information_material[0]['DurchschnittlichVerbrachteZeit']))
            total_time_spent_on_information_material_time = h_change_minutes_to_hours(round(total_time_spent_on_information_material[0]['GesamtzeitInfoMat'] ))
            text_to_print = text_to_print + "\n - " + average_time_spent_on_information_material_time + " mit Informationsseiten (insgesamt " + total_time_spent_on_information_material_time + " )"
        else:
            text_to_print = text_to_print + "\n - 0 Minuten mit Informationsseiten (Procedural Information und Supportive Information)"
        text_to_print = text_to_print + "\nverbracht. "

        print(text_to_print)
        if error_text != "":
            print("Achtung, im Rahmen der Funktion sind Fehler aufgetreten: \n" + error_text)
        return
    
    except Neo4jError as e:
        print("Im Rahmen der Funktion ist leider ein Neo4j-Fehler aufgetreten. ")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)

def print_content_of_learning_sessions(last_name):
    if h_test_if_student(last_name)==False:
        print("Scheinbar gibt es keinen Nutzer mit diesem Namen. Haben Sie sich vielleicht vertippt?")
        return

    info_mat, tasks = h_get_information_on_content(last_name)
    text_to_print = ""
    if not info_mat.empty:
        text_to_print = text_to_print + "\nIn den Lernsitzungen wurde das folgende Informationsmaterial bearbeitet: \n"
        session = tasks.iloc[0]['Lernsitzung']
        text_to_print = text_to_print + ("Lernsitzung am/um " + str(session) + ": \n")
        for index, row in tasks.iterrows():
            if row['Lernsitzung'] != session:
                session = row['Lernsitzung']
                text_to_print = text_to_print + "\nLernsitzung am/um " + str(session) + ": \n"
            text_to_print = text_to_print + " - " + row['Aufgabe'] + " (" + str(row['ZeitInMinuten']) + " Minuten) \n"

    if not tasks.empty:
        text_to_print = text_to_print + "\nIn den Lernsitzungen wurden die folgenden Aufgaben bearbeitet: \n"
        session = tasks.iloc[0]['Lernsitzung']
        text_to_print = text_to_print + ("Lernsitzung am/um " + str(session) + ": \n")
        for index, row in tasks.iterrows():
            if row['Lernsitzung'] != session:
                session = row['Lernsitzung']
                text_to_print = text_to_print + "\nLernsitzung am/um " + str(session) + ": \n"
            text_to_print = text_to_print + " - " + row['Aufgabe'] + " (" + str(row['ZeitInMinuten']) + " Minuten) \n"
        print(text_to_print)

# gibt die Reihenfolge aus, in der ein Studierender den Kurs bearbeitet hat
def print_learning_order_of_student_everything(last_name):
    if h_test_if_student(last_name)==False:
        print("Scheinbar gibt es keinen Nutzer mit diesem Namen. Haben Sie sich vielleicht vertippt?")
        return
    
    order = h_get_information_on_order(last_name)
    if order.empty:
        # Fehlermeldung schon in Funktion ausgegeben
        return
    
    print("Herr/Frau " + str(last_name) + " hat den Kurs in der folgenden Reihenfolge bearbeitet:")
    print(order)

# gibt Informationen zu Aufgaben aus, bei denen der Studierende viele Versuche mit wenigen Punkten abgegeben hat, das schlechteste Ergebnis erzielt hat usw.
def print_information_on_difficult_tasks_for_student(last_name):
    if h_test_if_student(last_name)==False:
        print("Scheinbar gibt es keinen Nutzer mit diesem Namen. Haben Sie sich vielleicht vertippt?")
        return
     
    try:
        with driver.session() as session:
            params = {"last_name" : last_name}
            difficult_tasks = session.run(""" 
                OPTIONAL MATCH (s:Student {last_name: $last_name})-[sw:struggled_with]->(lt:Learning_Task)
                WITH lt.title AS Aufgabe, count(sw) AS AnzahlSchwierigerVersuche 
                WHERE AnzahlSchwierigerVersuche <> 0
                RETURN Aufgabe, AnzahlSchwierigerVersuche ORDER BY AnzahlSchwierigerVersuche DESC""", params).data()
            worst_result = session.run("""
                OPTIONAL MATCH (s:Student {last_name: $last_name})-[sw:struggled_with]->(lt:Learning_Task)
                RETURN lt.title AS Aufgabe, sw.score AS Punktzahl ORDER BY Punktzahl ASC LIMIT 1""", params).data()
            most_attempts = session.run("""
                MATCH (s:Student {last_name: $last_name})-[r:successfully_solved|struggled_with]->(lt:Learning_Task)
                RETURN lt.title AS Aufgabe, count(r) AS ZahlVersuche ORDER BY ZahlVersuche DESC""", params).data()
            number_of_tasks_completed_without_attempt = session.run("""
                MATCH (s:Student {last_name: $last_name})-[c:completed]->(lt:Learning_Task)
                WHERE NOT EXISTS {(s)-[r:successfully_solved|struggled_with]->(lt)}
                RETURN COUNT(lt) AS ZahlAufgaben""", params).data()
            tasks_completed_without_attempt = session.run("""
                MATCH (s:Student {last_name: $last_name})-[c:completed]->(lt:Learning_Task)
                WHERE NOT EXISTS {(s)-[r:successfully_solved|struggled_with]->(lt)}
                RETURN lt.title AS Aufgabe""", params).data()
    
        text_to_print = ""
        if difficult_tasks and difficult_tasks[0]['AnzahlSchwierigerVersuche'] is not None:
            number_of_attempts_for_difficult_tasks = difficult_tasks[0]['AnzahlSchwierigerVersuche']
            difficult_tasks_list = []
            for row in difficult_tasks:
                if row['AnzahlSchwierigerVersuche'] == number_of_attempts_for_difficult_tasks:
                    difficult_tasks_list.append(row['Aufgabe'])
                else:
                    break
            text_to_print = text_to_print + "Die meisten Schwierigkeiten gab es scheinbar mit den Übungen " + (", ".join(difficult_tasks_list)) + ". Bei diesen Übungen hatte der Studierende die meisten Versuche mit wenigen Punkten. Im Detail:\n"
            
            for task in difficult_tasks_list: 
                last_result_for_task = h_get_students_last_result_for_task(last_name, task)
                if number_of_attempts_for_difficult_tasks == 1:
                    text_to_print = text_to_print +" - Bei Aufgabe " + str(task) + " hat der Studierende einen Versuch mit weniger als 80 Prozent der Punkte absolviert. "
                else:
                    text_to_print = text_to_print +" - Bei Aufgabe " + str(task) + " hat der Studierende " + str(number_of_attempts_for_difficult_tasks) + " Versuche mit weniger als 80 Prozent der Punkte absolviert. "
                number_of_successful_attempts = h_get_number_of_successful_attempts_for_task_and_student(last_name, task)
                if number_of_successful_attempts==1:
                    text_to_print = text_to_print +"Es wurde aber auch ein erfolgreicher Versuch aufgezeichnet. "
                elif number_of_successful_attempts>1:
                    text_to_print = text_to_print +"Es wurden aber auch " + str(number_of_successful_attempts) + " erfolgreiche Versuche aufgezeichnet. "
                text_to_print = text_to_print +"Das letzte Ergebnis bei Aufgabe " + str(task) + " war " + str(last_result_for_task) + " Punkte.\n" 

        if worst_result:
            worst_result_task = worst_result[0]['Aufgabe']
            worst_result_score = worst_result[0]['Punktzahl']
            text_to_print = text_to_print +"Der schlechteste Versuch insgesamt wurde bei Aufgabe " + worst_result_task + " unternommen. Es wurden " + str(worst_result_score) + " Punkte erzielt. "
            number_of_successful_attempts_after_worst_result = h_get_number_of_successful_attempts_for_task_and_student(last_name, worst_result_task)
            if number_of_successful_attempts_after_worst_result==1:
                    text_to_print = text_to_print +"Es wurde aber auch ein erfolgreicher Versuch aufgezeichnet. "
            elif number_of_successful_attempts_after_worst_result>1:
                    text_to_print = text_to_print +"Es wurden aber auch " + str(number_of_successful_attempts_after_worst_result) + " erfolgreiche Versuche aufgezeichnet. "
            last_result_for_worst_task = h_get_students_last_result_for_task(last_name, worst_result_task)
            text_to_print = text_to_print +"Das letzte Ergebnis bei Aufgabe " + worst_result_task + " war " + str(last_result_for_worst_task) + " Punkte.\n" 

        if most_attempts and most_attempts[0]['ZahlVersuche'] is not None:
            most_attempts_number = most_attempts[0]['ZahlVersuche']
            attempts_list = []
            last_results_list = []
            for row in most_attempts:
                if row['ZahlVersuche']==most_attempts_number:
                    attempts_list.append(row['Aufgabe'])
                    last_results_list.append(str(h_get_students_last_result_for_task(last_name, row['Aufgabe'])))
                else: 
                    break
            if len(attempts_list)==1:
                text_to_print = text_to_print + "Bei Aufgabe " + str(attempts_list[0]) + " hat der Studierende insgesamt die meisten Versuche unternommen (" + str(most_attempts_number) + "). Das Ergebnis des letzten Versuchs war " + str(last_results_list[0]) + " Punkte . "
            else:
                text_to_print = text_to_print + "Der Studierende hat die meisten Versuche bei den Aufgaben "
                text_to_print = text_to_print + (", ".join(attempts_list)) + " unternommen (jeweils " + str(most_attempts_number) + " Versuche). Das Ergebnis des letzten Versuchs bei der jeweiligen Aufgabe war respektive " +(", ".join(last_results_list)) + ".\n"

        if number_of_tasks_completed_without_attempt and number_of_tasks_completed_without_attempt[0]['ZahlAufgaben'] is not None:
            number_of_tasks_without_attempt = number_of_tasks_completed_without_attempt[0]['ZahlAufgaben']
            if number_of_tasks_without_attempt != 0:
                if tasks_completed_without_attempt:
                    tasks_completed_without_attempt_list = [record['Aufgabe'] for record in tasks_completed_without_attempt]
                    text_to_print = text_to_print +"Die " + h_grammar_correction_task(number_of_tasks_without_attempt) + str(tasks_completed_without_attempt_list) + h_grammar_correction_wurden(number_of_tasks_without_attempt==1) + "als \"abgeschlossen\" markiert, ohne dass ein Lösungsversuch abgegeben wurde."
            
        print(text_to_print)
        return

    except Neo4jError as e:
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return

# gibt Informationen zu einem Studierenden und einer spezifischen Aufgabe aus (ob abgeschlossen, Anzahl Versuche, Ergebnis ...)
def print_information_on_students_performance_with_task(last_name, task_name):
    if h_test_if_student(last_name)==False:
        print("Scheinbar gibt es keinen Nutzer mit diesem Namen. Haben Sie sich vielleicht vertippt?")
        return 

    if h_test_if_task(task_name)==False:
        print("Scheinbar gibt es keine Aufgabe mit diesem Namen. Haben Sie sich vielleicht vertippt?")
        return

    try: 
        text_to_print = "" 
        with driver.session() as session:
            params = {"last_name" : last_name, "task_name" : task_name}
            time_spent = session.run("""
                MATCH(s:Student {last_name: $last_name})-[]->(ls:Learning_Session)-[c:covered]->(lt:Learning_Task {title: $task_name})
                RETURN SUM(c.time_spent) AS Gesamtzeit""", params).data()
            completed = session.run("""
                MATCH(s:Student {last_name: $last_name})-[c:completed]->(lt:Learning_Task {title: $task_name})
                RETURN c.type AS Typ, c.score AS Punktzahl, c.completion_time AS Zeit""", params).data()
            number_of_attempts = session.run("""
                MATCH(s:Student {last_name: $last_name})-[r:struggled_with|successfully_solved]->(lt:Learning_Task {title: $task_name})
                RETURN COUNT(r) AS GesamtzahlVersuche""", params).data()
            number_of_successful_attempts = session.run("""
                MATCH(s:Student {last_name: $last_name})-[r:successfully_solved]->(lt:Learning_Task {title: $task_name})
                RETURN COUNT(r) AS GesamtzahlErfolgreicheVersuche""", params).data()

            if time_spent and time_spent[0]['Gesamtzeit'] is not None:
                total_time = h_change_minutes_to_hours(time_spent[0]['Gesamtzeit'])
                text_to_print = text_to_print + "Der Studierende hat sich insgesamt " + total_time + " mit der Aufgabe " + task_name + " beschäftigt. "
            else:
                text_to_print = text_to_print + "Der Studierende hat sich bisher nicht mit der Aufgabe beschäftigt. "
                print(text_to_print)
                return

            if completed and completed[0]['Typ'] is not None:
                if completed[0]['Typ']=="button":
                    text_to_print = text_to_print + "Der Studierende hat die Aufgabe über den \"Mark as done\"-Button als abgeschlossen markiert, jedoch keinen Lösungsversuch abgegeben. "
                else:
                    if number_of_attempts and number_of_attempts[0]['GesamtzahlVersuche'] is not None and number_of_successful_attempts and number_of_successful_attempts[0]['GesamtzahlErfolgreicheVersuche'] is not None:
                        total_number = number_of_attempts[0]['GesamtzahlVersuche']
                        success_number = number_of_successful_attempts[0]['GesamtzahlErfolgreicheVersuche']
                        text_to_print = text_to_print + "Es" + h_grammar_correction_wurden(total_number==1) + "ingesamt " + h_grammar_correction_attempt(total_number) + "unternommen. "
                        if success_number != 0:
                            text_to_print = text_to_print + "Davon" + h_grammar_correction_waren(success_number==1) + h_grammar_correction_attempt(success_number) + "erfolgreich. "
                    text_to_print = text_to_print + "Den letzten Lösungsversuch hat der Studierende am/um " + completed[0]['Zeit'].strftime('%Y-%m-%d %H:%M') + " unternommen. Dabei wurden " + str(round(completed[0]['Punktzahl'],1)) + " Punkte erzielt. "

            print(text_to_print)
            return
        
    except Neo4jError as e:
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return
  
# gibt Informationen dazu aus, wann ein Studierender sich das letzte Mal mit einem Skill beschäftigt hat (und auf welcher Taxonomiestufe) sowie wie viel Zeit er
# insgesamt auf das Üben dieses Skills verwendet hat
def print_last_practice_of_skill(last_name, skill_name):
    if h_test_if_student(last_name)==False:
        print("Scheinbar gibt es keinen Nutzer mit diesem Namen. Haben Sie sich vielleicht vertippt?")
        return
    
    skill_id = h_get_skill_id_for_name(skill_name)
    if skill_id== "":
        # Fehlermeldung wird schon in der Funktion ausgegeben
        return

    try: 
        with driver.session() as session:
            params = {"last_name" : last_name, "skill_name" : skill_name}
            last_practice = session.run("""
                MATCH(s:Student {last_name: $last_name})-[:did_learning_session]->(ls:Learning_Session)
                WITH ls
                MATCH (ls)-[c:covered]->(lt:Learning_Task)
                WITH c, lt
                MATCH (lt)-[r]->(sk:Skill {title: $skill_name})
                RETURN c.start_time AS Zeit, c.time_spent AS Dauer, lt.title AS inAufgabe, type(r) AS Taxonomiestufe ORDER BY Zeit DESC LIMIT 1""", params).data()
    
        if last_practice and last_practice[0]['Zeit'] is not None and last_practice[0]['Dauer'] is not None:
            last_timestamp = last_practice[0]['Zeit'].strftime('%Y-%m-%d %H:%M')
            duration = h_change_minutes_to_hours(last_practice[0]['Dauer'])
            task = last_practice[0]['inAufgabe']
            taxonomy_level = h_change_taxonomy_level_for_print(last_practice[0]['Taxonomiestufe'])
            print("Der Studierende hat den Skill \"" + skill_name + "\" zuletzt am " + last_timestamp + " für " + duration + " im Rahmen der Aufgabe " + task + " auf Taxonomiestufe \"" + taxonomy_level + "\" geübt.")

    except Neo4jError as e:
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return

    try: 
        with driver.session() as session:
            params = {"last_name" : last_name, "skill_name" : skill_name}
            total_practice = session.run("""
                MATCH(s:Student {last_name: $last_name})-[:did_learning_session]->(ls:Learning_Session)
                WITH ls
                MATCH (ls)-[c:covered]->(lt:Learning_Task)
                WITH c, lt
                MATCH (lt)-[r]->(sk:Skill {title: $skill_name})
                RETURN SUM(c.time_spent) AS ZeitInsgesamt, COUNT(DISTINCT lt) AS ZahlAufgaben""", params).data()
    
        if total_practice and total_practice[0]['ZeitInsgesamt'] is not None and total_practice[0]['ZahlAufgaben'] is not None:
            total_duration = h_change_minutes_to_hours(total_practice[0]['ZeitInsgesamt'])
            total_number_of_tasks = total_practice[0]['ZahlAufgaben']
            print("Insgesamt hat sich der Studierende " + total_duration + " in " + h_grammar_correction_task(total_number_of_tasks) + "mit dem Skill beschäftigt.")
                
    except Neo4jError as e:
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return

# gibt Informationen dazu aus, wann ein Studierender sich das letzte Mal mit einem Wissenselement beschäftigt hat (und in welcher Wissensdimension) sowie wie viel Zeit er
# insgesamt auf das Üben dieses Wissensbausteins verwendet hat
def print_last_practice_of_knowledge(last_name, knowledge_name):
    if h_test_if_student(last_name)==False:
        print("Scheinbar gibt es keinen Nutzer mit diesem Namen. Haben Sie sich vielleicht vertippt?")
        return
    
    knowledge_id = h_get_knowledge_id_for_name(knowledge_name)
    if knowledge_id == "":
        # Fehlermeldung bereits in der Funktion ausgegeben
        return

    try: 
        with driver.session() as session:
            params = {"last_name" : last_name, "knowledge_name" : knowledge_name}
            last_practice = session.run("""
                MATCH(s:Student {last_name: $last_name})-[:did_learning_session]->(ls:Learning_Session)
                WITH ls
                MATCH (ls)-[c:covered]->(lt:Learning_Task)
                WITH c, lt
                MATCH (lt)-[r]->(k:Knowledge {title: $knowledge_name})
                RETURN c.start_time AS Zeit, c.time_spent AS Dauer, lt.title AS inAufgabe, type(r) AS Wissensdimension ORDER BY Zeit DESC LIMIT 1""", params).data()
    
        if last_practice and last_practice[0]['Zeit'] is not None and last_practice[0]['Dauer'] is not None:
            last_timestamp = last_practice[0]['Zeit'].strftime('%Y-%m-%d %H:%M')
            duration = h_change_minutes_to_hours(last_practice[0]['Dauer'])
            task = last_practice[0]['inAufgabe']
            knowledge_dimension = h_change_knowledge_dimension_for_print(last_practice[0]['Wissensdimension'])
            print("Der Studierende hat die Wissenskomponente \"" + knowledge_name + "\" zuletzt am " + last_timestamp + " für " + duration + " im Rahmen der Aufgabe " + task + " in der Wissensdimension \"" + knowledge_dimension + "\" geübt.")

    except Neo4jError as e:
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return

    try: 
        with driver.session() as session:
            params = {"last_name" : last_name, "knowledge_name" : knowledge_name}
            total_practice = session.run("""
                MATCH(s:Student {last_name: $last_name})-[:did_learning_session]->(ls:Learning_Session)
                WITH ls
                MATCH (ls)-[c:covered]->(lt:Learning_Task)
                WITH c, lt
                MATCH (lt)-[r]->(kn:Knowledge {title: $knowledge_name})
                RETURN SUM(c.time_spent) AS ZeitInsgesamt, COUNT(DISTINCT lt) AS ZahlAufgaben""", params).data()          

        if total_practice:
            total_duration = h_change_minutes_to_hours(total_practice[0]['ZeitInsgesamt'])
            total_number_of_tasks = total_practice[0]['ZahlAufgaben']
            print("Insgesamt hat sich der Studierende " + total_duration + " in " + h_grammar_correction_task(str(total_number_of_tasks)) + "mit dem Wissensbaustein beschäftigt.")
        
    
    except Neo4jError as e:
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return  
    
    return  

# gibt Informationen dazu aus, wann ein Studierender sich das letzte Mal mit einer Kompetenz beschäftigt hat sowie wie viel Zeit er
# insgesamt auf das Üben dieser Kompetenz verwendet hat
def print_last_practice_of_competence(last_name, competence_name):
    if h_test_if_student(last_name)==False:
        print("Scheinbar gibt es keinen Nutzer mit diesem Namen. Haben Sie sich vielleicht vertippt?")
        return

    competence_id = h_get_competence_id_for_name(competence_name)
    if competence_id == "":
        # Fehlermeldung bereits in der Funktion ausgegeben
        return

    try: 
        with driver.session() as session:
            params = {"last_name" : last_name, "competence_name" : competence_name}
            last_practice = session.run("""
                MATCH(s:Student {last_name: $last_name})-[:did_learning_session]->(ls:Learning_Session)
                WITH ls
                MATCH (ls)-[c:covered]->(lt:Learning_Task)
                WITH c, lt
                MATCH (lt)<-[r]-(co:Competence {title: $competence_name})
                RETURN c.start_time AS Zeit, c.time_spent AS Dauer, lt.title AS inAufgabe ORDER BY Zeit DESC LIMIT 1""", params).data()

        if last_practice and last_practice[0]['Zeit'] is not None and last_practice[0]['Dauer'] is not None:
            last_timestamp = last_practice[0]['Zeit'].strftime('%Y-%m-%d %H:%M')
            duration = h_change_minutes_to_hours(last_practice[0]['Dauer'])
            task = last_practice[0]['inAufgabe']
            print("Der Studierende hat die Kompetenz \"" + competence_name + "\" zuletzt am " + last_timestamp + " für " + duration + " im Rahmen der Aufgabe " + task + " geübt.")

    except Neo4jError as e:
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
    
    try: 
        with driver.session() as session:
            params = {"last_name" : last_name, "competence_name" : competence_name}
            total_practice = session.run("""
                MATCH(s:Student {last_name: $last_name})-[:did_learning_session]->(ls:Learning_Session)
                WITH ls
                MATCH (ls)-[c:covered]->(lt:Learning_Task)
                WITH c, lt
                MATCH (lt)<-[r]-(co:Competence {title: $competence_name})
                RETURN SUM(c.time_spent) AS ZeitInsgesamt, COUNT(DISTINCT lt) AS ZahlAufgaben""", params).data()          

        if total_practice and total_practice[0]['ZeitInsgesamt'] is not None and total_practice[0]['ZahlAufgaben'] is not None:
            total_duration = h_change_minutes_to_hours(total_practice[0]['ZeitInsgesamt'])
            total_number_of_tasks = total_practice[0]['ZahlAufgaben']
            print("Insgesamt hat sich der Studierende " + total_duration + " in " + h_grammar_correction_task(total_number_of_tasks) + "mit der Kompetenz beschäftigt.")
        
    
    except Neo4jError as e:
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return  

## Info zu Kompetenz
def print_general_information_on_competence_from_id(competence_id):   
    competence_name = h_get_competence_name_for_id(competence_id)
    if competence_name == "":
        # Fehlermeldung bereits in Funktion ausgegeben
        return
    
    ausgabe = h_get_information_on_competence(competence_id)
    print(ausgabe)

    return

def print_general_information_on_competence_from_name(competence_name):
    competence_id = h_get_competence_id_for_name(competence_name)
    if competence_id == "":
        # Fehlermeldung bereits in Funktion ausgegeben
        return
    
    ausgabe = h_get_information_on_competence(competence_id)
    print(ausgabe)

    return

def print_difficulties_with_competences():
    try: 
        with driver.session() as session:
            tasks_with_most_attempts = session.run("""
                MATCH(c:Competence)-[r:is_taught_by]->(lt:Learning_Task)<-[sw:struggled_with]-(s:Student)
                RETURN c.title AS Kompetenz, COUNT(sw) AS ZahlVersuche ORDER BY ZahlVersuche DESC LIMIT 3""").data()
            
            if tasks_with_most_attempts:
                print("Bei den folgenden Kompetenzen gab es die meisten Versuche mit Schwierigkeiten (weniger als 80 Prozent der Punkte) bei den zugehörigen Aufgaben: \n")
                for record in tasks_with_most_attempts:
                    print(" - " + record['Kompetenz'] + " (" + str(record['ZahlVersuche']) + ") \n")
        
    except Neo4jError as e:
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return

## Info zu Wissensbaustein
def print_general_information_on_knowledge_from_id(knowledge_id):
    knowledge_name = h_get_knowledge_name_for_id(knowledge_id)
    if knowledge_name == "":
        # Fehlermeldung bereits in der Funktion ausgegeben
        return
    
    ausgabe = h_get_information_on_knowledge(knowledge_id)
    print(ausgabe)

    return

def print_general_information_on_knowledge_from_name(knowledge_name):
    knowledge_id = h_get_knowledge_id_for_name(knowledge_name)
    if knowledge_id == "":
        # Fehlermeldung bereits in der Funktion ausgegeben
        return
    
    ausgabe = h_get_information_on_knowledge(knowledge_id)
    print(ausgabe)

    return

def print_difficulties_with_knowledge_items():
    try: 
        with driver.session() as session:
            tasks_with_most_attempts = session.run("""
                MATCH(k:Knowledge)<-[r]-(lt:Learning_Task)<-[sw:struggled_with]-(s:Student)
                RETURN k.title AS Wissenselement, COUNT(sw) AS ZahlVersuche ORDER BY ZahlVersuche DESC LIMIT 3""").data()
            
            if tasks_with_most_attempts:
                print("Bei den folgenden Wissenselementen gab es die meisten Versuche mit Schwierigkeiten (weniger als 80 Prozent der Punkte) bei den zugehörigen Aufgaben: \n")
                for record in tasks_with_most_attempts:
                    print(" - " + record['Wissenselement'] + " (" + str(record['ZahlVersuche']) + ") \n")
        
    except Neo4jError as e:
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return

## Info zu Fähigkeit
def print_general_information_on_skill_from_id(skill_id):
    skill_name = h_get_skill_name_for_id(skill_id)
    if skill_name == "":
        # Fehlermeldung wird schon in der Funktion ausgegeben
        return
    
    ausgabe = h_get_information_on_skill(skill_id)
    print(ausgabe)

    return

def print_general_information_on_skill_from_name(skill_name):
    skill_id = h_get_skill_id_for_name(skill_name)
    if skill_id == "":
        # Fehlermeldung wird schon in der Funktion ausgegeben
        return
    
    ausgabe = h_get_information_on_skill(skill_id)
    print(ausgabe)
    return

def print_difficulties_with_skills():
    try: 
        with driver.session() as session:
            tasks_with_most_attempts = session.run("""
                MATCH(s:Skill)<-[r]-(lt:Learning_Task)<-[sw:struggled_with]-(st:Student)
                RETURN s.title AS Fähigkeit, COUNT(sw) AS ZahlVersuche ORDER BY ZahlVersuche DESC LIMIT 3""").data()
            
            if tasks_with_most_attempts:       
                print("Bei den folgenden Fähigkeiten gab es die meisten Versuche mit Schwierigkeiten (weniger als 80 Prozent der Punkte) bei den zugehörigen Aufgaben: \n")
                for record in tasks_with_most_attempts:
                    skill_name = record['Fähigkeit']
                    print(" - " + skill_name + " (" + h_get_skill_id_for_name(skill_name) + "), " + str(record['ZahlVersuche']) + " Versuche \n")
    
    except Neo4jError as e:
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return

###### Info zu Aufgabe
# gibt allgemeine Informationen zu einer Aufgabe aus - welche Fähigkeiten, Wissenselemente und Kompetenzen sie verwendet, wie viele Studierende sie 
# bearbeitet haben, wie viele Versuche es gab, wie viel Zeit durchschnittlich mit ihr verbracht wurde, welche falschen Antworten es gab ...
def print_general_information_on_task(task_name):  
    if h_test_if_task(task_name)==False:
        print("Scheinbar gibt es keine Aufgabe mit diesem Namen. Haben Sie sich vielleicht vertippt?")
        return

    try:
        with driver.session() as session:
            params = {"task_name" : task_name} 
            students_with_perfect_records_with_redos = session.run("""
                MATCH (s: Student)-[r:successfully_solved|struggled_with]->(lt:Learning_Task {title: $task_name})
                WITH s, r, lt
                ORDER BY r.timestamp
                WITH s, lt, COLLECT(r)[0] AS ErsterVersuch
                WHERE ErsterVersuch.score = 10
                WITH s, lt
                MATCH (s)-[r2:successfully_solved|struggled_with]->(lt)
                RETURN s.last_name AS Student, COUNT(r2) AS VersucheGesamt""", params).data() 
            average_number_of_attempts = session.run("""
                MATCH (s:Student)-[r:successfully_solved|struggled_with]->(lt:Learning_Task {title: $task_name})
                WITH s, COUNT(r) AS ZahlVersuche
                RETURN AVG(ZahlVersuche) AS DurchschnittlicheZahlVersuche""", params).data()                                                                  
        
        number_of_students = h_get_number_of_enrolled_students()
        if number_of_students == 0:
            print("Da keine Studierenden im Kurs eingeschrieben sind, hat niemand die Aufgabe " + task_name + " bearbeitet.")
            return
        
        text_to_print = ""
        text_to_print = text_to_print + h_get_competences_taught_in_task(task_name) + "\n"
        text_to_print = text_to_print + h_get_knowledge_taught_in_task(task_name) + "\n"
        text_to_print = text_to_print + h_get_skills_taught_in_task(task_name) + "\n"

        number_of_students_covering_task = h_get_number_of_students_covering_task(task_name)
        number_of_students_solving_task = h_get_number_of_students_making_attempt_for_task(task_name)

        percentage_of_students_covering_task = round(number_of_students_covering_task / number_of_students *100)
        percentage_of_students_solving_task = round(number_of_students_solving_task / number_of_students *100)
        text_to_print = text_to_print + "Die Aufgabe " + str(task_name) + " wurde von " + str(percentage_of_students_covering_task) + " Prozent der Studierenden aufgerufen und " + str(percentage_of_students_solving_task) + " Prozent der Studierenden haben mindestens einen Lösungsversuch unternommen. "
            
        average_time_spent_on_task = h_get_average_time_spent_on_task(task_name)
        total_time_spent_on_task =  h_get_total_time_spent_on_task(task_name)
        total_time_print = h_change_minutes_to_hours(total_time_spent_on_task)
        text_to_print = text_to_print + "Im Durchschnitt haben die Studierenden " + str(average_time_spent_on_task) + " Minuten auf der Seite verbracht und ingesamt " + total_time_print + ". "

        if average_number_of_attempts and average_number_of_attempts[0]['DurchschnittlicheZahlVersuche'] is not None:
            average_number_of_attempts_print = str(round(average_number_of_attempts[0]['DurchschnittlicheZahlVersuche'],1))
        else:
            average_number_of_attempts_print = "(Fehler bei der Berechnung)"
        number_of_attempts = h_get_number_of_attempts_for_task(task_name)
        number_of_successful_attempts = h_get_number_of_successful_attempts_for_task(task_name)
        text_to_print = text_to_print + "Durchschnittlich wurden von den Studierenden, die die Aufgabe bearbeitet haben, " + average_number_of_attempts_print + " Versuche eingereicht. Insgesamt wurden " + str(number_of_attempts) + " Lösungsversuche zu der Aufgabe abgegeben, davon " + str(number_of_successful_attempts) + " mit 80 oder mehr Prozent der erreichbaren Punkte. "
        
        number_of_students_with_perfect_record = h_get_number_of_students_with_perfect_record_for_task(task_name)
        percentage_of_students_with_perfect_record = round((number_of_students_with_perfect_record / number_of_students *100), 1)
        text_to_print = text_to_print + str(percentage_of_students_with_perfect_record) + " Prozent der Studierenden haben direkt im ersten Lösungsversuch 100 Prozent der Punkte erreicht. "

        if percentage_of_students_with_perfect_record != 0:
            number_of_perfect_record_students_with_redos = 0
            for record in students_with_perfect_records_with_redos:
                if record['VersucheGesamt']>1:
                    number_of_perfect_record_students_with_redos = number_of_perfect_record_students_with_redos+1
            text_to_print = text_to_print + "Davon haben " + str(number_of_perfect_record_students_with_redos) + " Prozent die Aufgabe trotzdem ein weiteres Mal bearbeitet. "

        average_result = h_get_average_result_for_task(task_name)
        text_to_print = text_to_print + "Durchschnittlich wurden " + str(average_result) + " Punkte erreicht. "

        # Die Antworten können aufgrund der Struktur der Logdateien nur beim letzten abgegebenen Versuch abgerufen werden. Nur wenn der letzte Versuch ein Versuch mit weniger als 80% war, können daher die Fehler ermittelt werden.
        text_about_wrong_answers = h_get_wrong_answers_for_task(task_name)
        if text_about_wrong_answers != "":
            text_to_print = text_to_print + " " + text_about_wrong_answers
 
        number_of_completed_without_attempts = h_get_number_of_completed_without_attempts(task_name)
        text_to_print = text_to_print + h_grammar_correction_student_nom(number_of_completed_without_attempts) + h_grammar_correction_haben(number_of_completed_without_attempts==1) + "die Aufgabe über den \"Mark as done\"-Button abgeschlossen, ohne einen Lösungsversuch abzugeben."

        print(text_to_print)
        return 

    except Neo4jError as e:
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return

###### Info zu Informationsmaterial (SI und PI)
# gibt allgemeine Informationen zu Informationsmaterial (Procedural Information und Supportive 
# Information) aus - wie viele Studierende es bearbeitet oder als abgeschlossen markiert haben, wie viel Zeit durchschnittlich damit verbracht wurde ...
def print_general_information_on_information_material(im_name):    
    if h_test_if_im(im_name) == False:
        print("Scheinbar gibt es keine Informationsseite mit diesem Namen. Haben Sie sich vielleicht vertippt?")
        return

    try:
        with driver.session() as session:
            params = {"im_name" : im_name}
            number_of_students_covering_im = session.run("""
                MATCH (s:Student)-[]->(ls:Learning_Session)-[c:covered]->(im:Information_Material {title: $im_name}) 
                RETURN COUNT(DISTINCT s) AS ZahlStudierender""", params).data()
            number_of_students_completing_im = session.run("""
                MATCH (s:Student)-[c:completed]->(im:Information_Material {title: $im_name}) 
                RETURN COUNT(DISTINCT s) AS ZahlStudierender""", params).data()
        
        text_to_print = ""
        error_text = ""

        number_of_students = h_get_number_of_enrolled_students()
        if number_of_students_covering_im and number_of_students_completing_im and number_of_students_covering_im[0]['ZahlStudierender'] is not None and number_of_students_completing_im[0]['ZahlStudierender'] is not None:
            number_of_students_covering_im = number_of_students_covering_im[0]['ZahlStudierender']
            number_of_students_completing_im = number_of_students_completing_im[0]['ZahlStudierender']
            percentage_of_students_covering_im = round(number_of_students_covering_im / number_of_students *100)
            percentage_of_students_completing_im = round(number_of_students_completing_im / number_of_students *100)
            text_to_print = "Die Informationsseite " + str(im_name) + " wurde von " + str(percentage_of_students_covering_im) + " Prozent der Studierenden aufgerufen und " + str(percentage_of_students_completing_im) + " Prozent der Studierenden haben die Seite als \"abgeschlossen\" markiert. "
        else:
            error_text = "Es ist ein Fehler aufgetreten bei der Ermittlung der Zahl der Studierenden, die die Aufgabe bearbeitet oder abgeschlossen haben. " 

        average_time_spent_on_im = h_get_average_time_spent_on_im(im_name)   
        total_time_spent_on_im=  h_get_total_time_spent_on_im(im_name)
        total_time_spent_on_im_print = h_change_minutes_to_hours(total_time_spent_on_im)
        text_to_print = text_to_print + "Im Durchschnitt haben die Studierenden " + str(average_time_spent_on_im) + " Minuten auf der Seite verbracht und insgesamt " + total_time_spent_on_im_print + ". "

        print(text_to_print)
        if error_text != "":
            print(error_text)

    except Neo4jError as e:
        print("Es ist ein Neo4j-Fehler aufgetreten: ")
        print("Neo4j error code: " + str(e.code) + ", ")
        if e.message is not None:
            print("Exception message: " + e.message)

###### Info zu Kurs
# gibt Informationen zu Aufgaben aus, die scheinbar schwierig waren
def print_information_on_difficult_tasks():
    try:
        with driver.session() as session:
            tasks_with_most_difficult_attempts = session.run("""
                MATCH ()-[sw:struggled_with]->(lt:Learning_Task)
                RETURN lt.title AS Aufgabe, COUNT(sw) AS AnzahlVersuche ORDER BY AnzahlVersuche DESC""") .data()
            worst_attempts_altogether = session.run("""
                OPTIONAL MATCH (s:Student)-[sw:struggled_with]->(lt:Learning_Task)
                WITH s.last_name AS Student, sw.score AS Punktzahl, lt.title AS Aufgabe
                RETURN Student, Punktzahl, Aufgabe ORDER BY Punktzahl""").data()
            worst_result_altogether = session.run("""
                MATCH(s:Student)-[r:successfully_solved|struggled_with]->(lt:Learning_Task)
                RETURN lt.title AS Aufgabe, AVG(r.score) AS Durchschnittsergebnis ORDER BY Durchschnittsergebnis""").data()
        
        text_to_print = ""
        error_text = ""
        most_difficult_tasks_list = []
        worst_attempts_list = []
        if tasks_with_most_difficult_attempts and tasks_with_most_difficult_attempts[0]['AnzahlVersuche'] is not None:
            number_most_attempts = tasks_with_most_difficult_attempts[0]['AnzahlVersuche']    
        else:
            number_most_attempts = 0
            error_text = error_text + "Es ist ein Fehler bei der Ermittlung der Aufgabe mit den meisten Lösungsversuchen mit weniger als 80 Prozent der Punkte aufgetreten. "
    
        if number_most_attempts > 1:
            for record in tasks_with_most_difficult_attempts:
                if record['AnzahlVersuche'] == number_most_attempts:
                    most_difficult_tasks_list.append(record['Aufgabe'])
                else:
                    break
            text_to_print = text_to_print + "Die meisten Lösungsversuche mit weniger als 80 Prozent der Punkte wurden für die folgende(n) Aufgabe(n) abgegeben: \n" +  (", ".join(most_difficult_tasks_list)) + " (je " + str(number_most_attempts) + " Versuche mit weniger als 80 Prozent). "

            for attempt_index in range (0, len(most_difficult_tasks_list)):
                name_of_task = str(most_difficult_tasks_list[attempt_index])
                text_about_wrong_answers = h_get_wrong_answers_for_task(name_of_task)
                if text_about_wrong_answers != "":
                    text_to_print = text_to_print + " " + text_about_wrong_answers
                total_number_of_attempts = h_get_number_of_attempts_for_task(name_of_task)
                text_to_print = text_to_print + "Insgesamt gab es zur Aufgabe " + name_of_task + " " + str(total_number_of_attempts) + " Versuche. "
                average_result_for_task = h_get_average_result_for_task(name_of_task)
                text_to_print = text_to_print + "Durchschnittlich wurden " + str(average_result_for_task) + " Punkte erzielt. "

        if worst_attempts_altogether and worst_attempts_altogether[0]['Punktzahl'] is not None:
            worst_attempt_score = worst_attempts_altogether[0]['Punktzahl']
        else:
            worst_attempt_score = 0
            error_text = error_text + "Es ist ein Fehler bei der Ermittlung des Ergebnisses des schwächsten Versuches aufgetreten. "

        student_with_worst_attempts_list = []
        if worst_attempts_altogether is not None:
            for record in worst_attempts_altogether:
                if record['Punktzahl'] == worst_attempt_score:
                    worst_attempts_list.append(record['Aufgabe'])
                    student_with_worst_attempts_list.append(record['Student'])
                else:
                    break

        if len(worst_attempts_list)==1:
            task_name = str(worst_attempts_list[0])
            student_name = str(student_with_worst_attempts_list[0])
            text_to_print = text_to_print + "\n\nDer Versuch mit den wenigsten Punkten wurde bei der Aufgabe " + task_name + " unternommen (" + str(worst_attempt_score) + " Punkte). "
            
            number_of_successful_attempts = h_get_number_of_successful_attempts_for_task_and_student(student_name, task_name)
            if number_of_successful_attempts==1:
                text_to_print = text_to_print + "Der Studierende hat aber bei der Aufgabe auch einen erfolgreichen Versuch unternommen. "
            elif number_of_successful_attempts>1:
                text_to_print = text_to_print + "Es wurden aber für den Studierenden auch " + str(number_of_successful_attempts) + " erfolgreiche Versuche aufgezeichnet. "
            else:
                text_to_print = text_to_print + "Der betreffende Studierende hat danach keinen besseren Versuch mehr eingereicht. "

            last_result_for_task = h_get_students_last_result_for_task(student_name, task_name)
            if last_result_for_task > worst_attempt_score:
                text_to_print = text_to_print + "Zum Schluss hat der Studierende mit " + str(last_result_for_task) + " Punkten ein besseres Ergebnis bei der Aufgabe erzielt. "
            if last_result_for_task == worst_attempt_score:
                response = h_get_students_last_response_for_task(student_name, task_name)
                if response != "":
                    text_to_print = text_to_print + "Die Antwort, die der Studierende abgegeben hat, war: " + str(response) + ". "

            average_result_for_task = h_get_average_result_for_task(task_name)
            text_to_print = text_to_print + "Im Durchschnitt wurden bei dieser Aufgabe " + str(average_result_for_task) + " Punkte erzielt. "

        elif len(worst_attempts_list)>1:
            text_to_print = text_to_print + "\n\nDie Versuche mit den wenigsten Punkten wurden bei den Aufgaben " + (", ".join(worst_attempts_list)) + " unternommen (je " + str(worst_attempt_score) + " Punkte).\n"
            for attempt_index in range (0, len(worst_attempts_list)):
                task_name = str(worst_attempts_list[attempt_index])
                student_name = str(student_with_worst_attempts_list[attempt_index])
                number_of_successful_attempts = h_get_number_of_successful_attempts_for_task_and_student(student_name, task_name)
                if number_of_successful_attempts==1:
                    text_to_print = text_to_print + "Bei Aufgabe " + task_name + " hat der betreffende Studierende auch einen erfolgreichen Versuch unternommen. "
                elif number_of_successful_attempts>1:
                    text_to_print = text_to_print + "Bei Aufgabe " + task_name + " wurden für den betreffenden Studierenden auch " + str(number_of_successful_attempts) + " erfolgreiche Versuche aufgezeichnet. "
                else:
                    text_to_print = text_to_print + "Bei Aufgabe " + task_name +  " hat der betreffende Studierende keinen besseren Versuch mehr eingereicht. "

                last_result_for_task = h_get_students_last_result_for_task(student_name, task_name)
                if last_result_for_task > worst_attempt_score:
                    text_to_print = text_to_print + "Zum Schluss hat der Studierende mit " + str(last_result_for_task) + " Punkten ein besseres Ergebnis bei der Aufgabe erzielt. "
                if last_result_for_task == worst_attempt_score:
                    response = h_get_students_last_response_for_task(student_name, task_name)
                    if response != "":
                        text_to_print = text_to_print + "Die Antwort, die der Studierende abgegeben hat, war: " + str(response) + ". "

                average_result_for_task = h_get_average_result_for_task(task_name)
                text_to_print = text_to_print + "Im Durchschnitt wurden bei der Aufgabe " + task_name + " " + str(average_result_for_task) + " Punkte erzielt.\n"

        if worst_result_altogether and worst_result_altogether[0]['Durchschnittsergebnis'] is not None:
            worst_result_score = worst_result_altogether[0]['Durchschnittsergebnis']
            worst_result_task_list = []
            for row in worst_result_altogether:
                if row['Durchschnittsergebnis']== worst_result_score:
                    worst_result_task_list.append(row['Aufgabe'])
                else:
                    break
            text_to_print = text_to_print + "\nDas schlechteste Durchschnittsergebnis wurde mit " + str(round(worst_result_score,1)) + " Punkten bei " + (", ".join(worst_result_task_list)) + " erzielt. "
       
        print(text_to_print)
        if error_text != "":
            print("Achtung: Es sind im Rahmen der Abfrage Fehler aufgetreten: \n" + error_text)
        
    except Neo4jError as e:
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        print("In der Funktion ist ein Neo4j-Fehler aufgetreten.")

# gibt Informationen zur durchschnittlichen Punktzahl und zum/zur besten Studierenden sowie dessen/deren Bearbeitungsreihenfolge aus und generiert einen Scatterplot zur
# möglichen Korrelation der erreichten Gesamtpunktzahl und der im Kurs verbrachten Zeit
def print_information_on_success_in_course():
    try:
        with driver.session() as session: 
            total_score_and_time_cypher = session.run(""" 
                MATCH (s:Student)-[d:did_learning_session]->(ls:Learning_Session)
                WITH s, SUM(duration.between(ls.start_time, ls.end_time).MINUTES) AS GesamtzeitImKurs
                MATCH (s)-[c:completed]->(lt:Learning_Task)
                WITH s, GesamtzeitImKurs, SUM(c.score) AS Gesamtpunktzahl
                RETURN s.st_ID AS Studierender, GesamtzeitImKurs, Gesamtpunktzahl""")
            average_points = session.run("""
                    MATCH (s:Student)-[c:completed]->(lt:Learning_Task)
                    WITH s.st_ID AS Student, SUM(c.score) AS Gesamtpunktzahl
                    RETURN AVG(Gesamtpunktzahl) AS DurchschnittGesamtpunkte""").data()
            best_student_with_points = session.run("""
                    MATCH (s:Student)-[c:completed]->(lt:Learning_Task)
                    WITH s.last_name AS Student, SUM(c.score) AS Gesamtpunktzahl
                    RETURN Student, Gesamtpunktzahl ORDER BY Gesamtpunktzahl DESC LIMIT 1""").data()
            
        text_to_print = ""
        error_text = ""

        if average_points and average_points[0]['DurchschnittGesamtpunkte'] is not None:
            average_total_points = round(average_points[0]['DurchschnittGesamtpunkte'])
            number_of_learning_tasks = h_get_number_of_learning_tasks()
            max_score = number_of_learning_tasks*10
            text_to_print = text_to_print + "Im Durchschnitt haben die Studierenden im Kurs rund " + str(average_total_points) + " Punkte erzielt. Bei " + str(number_of_learning_tasks) + " Aufgaben im Kurs lag die Maximalpunktzahl bei " + str(max_score) + " Punkten. "
        
        else:
            average_total_points = 0
            error_text = error_text + "Bei der Berechnung der durchschnittlichen Gesamtpunktzahl ist ein Fehler aufgetreten. "

        print(text_to_print)

        if best_student_with_points and best_student_with_points[0]['Student'] is not None and best_student_with_points[0]['Gesamtpunktzahl'] is not None:
            best_student = best_student_with_points[0]['Student']
            best_score = round(best_student_with_points[0]['Gesamtpunktzahl'])
            print("Die höchste Punktzahl hat mit rund " + str(best_score) + " Punkten Herr/Frau " + str(best_student) + " erreicht. ")
            print_learning_order_of_student_everything(best_student)
        else:
            best_student = ""
            error_text = error_text + "Bei der Ermittlung des erfolgreichsten Studierenden ist ein Fehler aufgetreten. "

        if total_score_and_time_cypher:
            data_for_plot = [record.data() for record in total_score_and_time_cypher]
            total_score_and_time_per_student = pd.DataFrame(data_for_plot)  

            plt.figure(figsize=(8,6))
            plt.scatter(total_score_and_time_per_student['GesamtzeitImKurs'], total_score_and_time_per_student['Gesamtpunktzahl'])
            plt.title('Korrelation zwischen im Kurs verbrachter Zeit und erzielter Gesamtpunktzahl')
            plt.xlabel('Im Kurs verbrachte Minuten')
            plt.ylabel('Erzielte Punkte')
            plt.savefig('output/corr_time_result.png')
            print('Eine Grafik zur Korrelation zwischen im Kurs verbrachter Zeit und Gesamtergebnis ist zu finden unter graph-container/shared_data/images/corr_time_result.png')
            plt.clf()
            plt.close()

        if error_text != "":
            print("Achtung, innerhalb der Funktion sind Fehler aufgetreten: \n" + error_text)

    except Neo4jError as e:
        print("Leider ist ein Neo4j-Fehler aufgetreten.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)

## Info zur Zeit im Kurs
# gibt allgemeine Informationen zur im Kurs verbrachten Zeit aus
def print_information_on_time_spent_in_course():
    try:
        with driver.session() as session:
            total_time_spent_in_course = session.run("""
                MATCH ()-[:did_learning_session]->(ls:Learning_Session)
                WITH duration.between(datetime(ls.start_time), datetime(ls.end_time)) AS MinutenImKurs
                RETURN SUM(MinutenImKurs) AS Gesamtzeit""").data()
            average_time_spent_in_course = session.run("""
                MATCH (s:Student)-[:did_learning_session]->(ls:Learning_Session)
                WITH s, SUM(duration.between(datetime(ls.start_time), datetime(ls.end_time))) AS MinutenImKurs
                RETURN AVG(MinutenImKurs) AS DurchschnittlicheMinutenImKurs""").data()
            total_number_of_learning_sessions = session.run("""
                MATCH (s:Student)-[r:did_learning_session]->(ls:Learning_Session)
                RETURN COUNT(ls) AS GesamtzahlLernsitzungen""").data()
            average_number_of_learning_sessions = session.run("""
                MATCH (s:Student)-[r:did_learning_session]->(ls:Learning_Session)
                WITH s AS Student, COUNT(ls) AS Anzahl
                RETURN toInteger(AVG(Anzahl)) AS DurchschnittlicheAnzahlLernsitzungen""").data()
            average_length_of_learning_session = session.run("""
                MATCH (ls:Learning_Session)
                WITH ls.ls_ID AS Session, duration.between(datetime(ls.start_time), datetime(ls.end_time)) AS DauerLernsitzung
                RETURN AVG(DauerLernsitzung) AS DurchschnittlicheDauerLernsitzung""").data()
            total_time_spent_on_tasks = session.run("""
                MATCH (ls:Learning_Session)-[c:covered]->(lt:Learning_Task)
                RETURN toInteger(SUM(c.time_spent)) AS GesamtzeitAufgaben""").data()
            total_time_spent_on_pi = session.run("""
                MATCH (ls:Learning_Session)-[c:covered]->(pi:Procedural_Information)
                RETURN toInteger(SUM(c.time_spent)) AS GesamtzeitPI""").data()
            total_time_spent_on_si = session.run("""
                MATCH (ls:Learning_Session)-[c:covered]->(si:Supportive_Information)
                RETURN toInteger(SUM(c.time_spent)) AS GesamtzeitSI""").data()
            first_learning_session_start_time = session.run("""
                MATCH (s:Student)-[r:did_learning_session]->(ls:Learning_Session)
                WITH ls.start_time AS Startzeit
                RETURN Startzeit ORDER BY Startzeit ASC LIMIT 1""").data()
            last_learning_session_end_time = session.run("""
                MATCH (s:Student)-[r:did_learning_session]->(ls:Learning_Session)
                WITH ls.end_time AS Endzeit
                RETURN Endzeit ORDER BY Endzeit DESC LIMIT 1""").data()
            most_time_spent = session.run("""
                MATCH(s:Student)-[]->(ls:Learning_Session)-[c:covered]->(m)
                RETURN SUM(c.time_spent) AS Gesamtzeit, m.title AS Material ORDER BY Gesamtzeit DESC LIMIT 1""").data()
            least_time_spent = session.run("""
                MATCH(s:Student)-[]->(ls:Learning_Session)-[c:covered]->(m)
                WITH m, SUM(c.time_spent) AS Gesamtzeit
                RETURN m.title AS Material, Gesamtzeit ORDER BY Gesamtzeit ASC LIMIT 1""").data()
            not_visited = session.run("""
                MATCH (m:Learning_Task|Information_Material)
                WHERE NOT (m)<-[:covered]-(:Learning_Session)
                RETURN m.title AS Material""").data()
            cypher_for_plot = session.run(""" 
                MATCH(s)-[]->(ls:Learning_Session)
                RETURN ls.start_time AS Startzeit, ls.end_time AS Endzeit, duration.between(ls.start_time, ls.end_time).MINUTES AS Dauer""")
            data_for_plot = [record.data() for record in cypher_for_plot]
            
        
        if data_for_plot!=[]:
            learning_sessions = pd.DataFrame(data_for_plot)
        else:
            learning_sessions = pd.DataFrame()

        error_text = ""
        text_to_print = ""

        if total_time_spent_in_course and total_time_spent_in_course[0]['Gesamtzeit'] is not None:
            total_time_spent_in_course = h_normalize_duration(total_time_spent_in_course[0]['Gesamtzeit'])
        else:
            total_time_spent_in_course = str(0)
            error_text = error_text + "Es ist ein Fehler bei der Berechnung der Gesamtzeit im Kurs aufgetreten. "

        if  total_number_of_learning_sessions and total_number_of_learning_sessions[0]['GesamtzahlLernsitzungen'] is not None:
            total_number_of_learning_sessions = total_number_of_learning_sessions[0]['GesamtzahlLernsitzungen']
        else: 
            total_number_of_learning_sessions = total_number_of_learning_sessions[0]['GesamtzahlLernsitzungen']
            error_text = error_text + "Es ist ein Fehler bei der Berechnung der Gesamtzahl von Lernsitzungen aufgetreten. "

        text_to_print = text_to_print + "Die Studierenden haben insgesamt " + total_time_spent_in_course + " in " + str(total_number_of_learning_sessions) + " Lernsitzungen im Kurs verbracht. "

        if total_time_spent_on_tasks and total_time_spent_on_tasks[0]['GesamtzeitAufgaben'] is not None:
            total_time_spent_on_tasks_int = total_time_spent_on_tasks[0]['GesamtzeitAufgaben']
            total_time_spent_on_tasks_print = h_change_minutes_to_hours(total_time_spent_on_tasks_int)
        else: 
            total_time_spent_on_tasks_print = "0 Minuten "
            error_text = error_text + "Es ist ein Fehler bei der Berechnung der mit Aufgaben verbrachten Gesamtzeit aufgetreten. "

        if total_time_spent_on_pi and total_time_spent_on_pi[0]['GesamtzeitPI'] is not None:
            total_time_spent_on_pi_int = total_time_spent_on_pi[0]['GesamtzeitPI']
            total_time_spent_on_pi_print = h_change_minutes_to_hours(total_time_spent_on_pi_int)
        else:
            total_time_spent_on_pi_print = "0 Minuten "
            error_text = error_text + "Es ist ein Fehler bei der Berechnung der mit Procedural Information-Material verbrachten Gesamtzeit aufgetreten. "

        if total_time_spent_on_si and total_time_spent_on_si[0]['GesamtzeitSI'] is not None:
            total_time_spent_on_si_int = total_time_spent_on_si[0]['GesamtzeitSI']
            total_time_spent_on_si_print = h_change_minutes_to_hours(total_time_spent_on_si_int)
        else:
            total_time_spent_on_si_print = "0 Minuten "
            error_text = error_text + "Es ist ein Fehler bei der Berechnung der mit Supportive Information-Material verbrachten Gesamtzeit aufgetreten. "

        text_to_print = text_to_print + "Davon sind " + total_time_spent_on_tasks_print + " auf Lernaufgaben, " + total_time_spent_on_pi_print + " auf Procedural Information-Seiten und " + total_time_spent_on_si_print + " auf Supportive Information-Seiten entfallen. "

        if first_learning_session_start_time:
            first_learning_session_start_time = first_learning_session_start_time[0]['Startzeit'].strftime('%Y-%m-%d %H:%M')
        else:
            first_learning_session_start_time = str(0)
            error_text = error_text + "Es ist ein Fehler bei der Berechnung der Startzeit der ersten Lernsitzung aufgetreten. "
        if last_learning_session_end_time and last_learning_session_end_time[0]['Endzeit'] is not None:
            last_learning_session_end_time = last_learning_session_end_time[0]['Endzeit'].strftime('%Y-%m-%d %H:%M')
        else:
            last_learning_session_end_time = str(0)
            error_text = error_text + "Es ist ein Fehler bei der Berechnung der Endzeit der letzten Lernsitzung aufgetreten. "
 
        text_to_print = text_to_print + "Der erste Aufruf fand am/um " + first_learning_session_start_time + " Uhr, der letzte Aufruf am/um " + last_learning_session_end_time + " Uhr statt. "
        
        if average_time_spent_in_course and average_time_spent_in_course[0]['DurchschnittlicheMinutenImKurs'] is not None:
            average_time_spent_in_course_print = h_normalize_duration(average_time_spent_in_course[0]['DurchschnittlicheMinutenImKurs'])
        else:
            average_time_spent_in_course = str(0)
            error_text = error_text + " Es ist ein Fehler bei der Berechnung der durchschnittlich im Kurs verbrachten Zeit aufgetreten. "

        if average_number_of_learning_sessions and average_number_of_learning_sessions[0]['DurchschnittlicheAnzahlLernsitzungen'] is not None:
            average_number_of_learning_sessions = average_number_of_learning_sessions[0]['DurchschnittlicheAnzahlLernsitzungen']
        else: 
            average_number_of_learning_sessions = 0
            error_text = error_text + " Es ist ein Fehler bei der Berechnung der durchschnittlichen Anzahl von Lernsitzungen. aufgetreten. "
        
        text_to_print = text_to_print + "Durchschnittlich hat jeder Student" + average_time_spent_in_course_print + "in " + str(average_number_of_learning_sessions) + " Lernsitzungen im Kurs verbracht. "

        if average_length_of_learning_session and average_length_of_learning_session[0]['DurchschnittlicheDauerLernsitzung'] is not None:
            average_length_of_learning_session_print = h_normalize_duration(average_length_of_learning_session[0]['DurchschnittlicheDauerLernsitzung'])
        else:
            average_length_of_learning_session = 0
            error_text = error_text + " Es ist ein Fehler bei der Berechnung der durchschnittlichen Dauer von Lernsitzungen. aufgetreten. "

        text_to_print = text_to_print + "Eine Lernsitzung hat dabei im Durchschnitt" + average_length_of_learning_session_print + "gedauert."

        print(text_to_print)
        if error_text != "":
            print("Achtung - es sind Fehler aufgetreten! \n" + error_text)
        text_to_print = ""
        error_text = ""

        if not learning_sessions.empty:
            learning_sessions['Startzeit'] = learning_sessions['Startzeit'].apply(lambda x: x.to_native() if hasattr(x, 'to_native') else x)
            learning_sessions['Endzeit'] = learning_sessions['Endzeit'].apply(lambda x: x.to_native() if hasattr(x, 'to_native') else x)
            learning_sessions['Startzeit'] = pd.to_datetime(learning_sessions['Startzeit'])
            learning_sessions['Endzeit'] = pd.to_datetime(learning_sessions['Endzeit']) 

            learning_sessions['Woche'] = learning_sessions['Startzeit'].dt.to_period('W')
            weekly_data = learning_sessions.groupby('Woche')['Dauer'].sum().reset_index()
            weekly_data['Woche'] = weekly_data['Woche'].astype(str)
            
            plt.figure(figsize=(10, 6))
            sns.barplot(x='Woche', y='Dauer', data=weekly_data, color='#2cb794')
            plt.title('Zeit im Kurs pro Woche')
            plt.xlabel('Woche')
            plt.ylabel('Gesamtzeit (Minuten)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig('output/learning_time_total.png')
            print('Eine Darstellung der Verteilung der Lernzeit auf die Kurswochen ist zu finden unter graph-container/shared_data/images/learning_time_total.png')
            plt.clf()
            plt.close()

        if most_time_spent:
            most_time_spent_on_material = most_time_spent[0]['Gesamtzeit']
            most_time_spent_on_material_print = h_change_minutes_to_hours(most_time_spent_on_material)
            material_most_time_spent_on = most_time_spent[0]['Material']
        
            if h_test_if_task(material_most_time_spent_on):
                average_time_spent = h_get_average_time_spent_on_task(material_most_time_spent_on)
                average_time_spent_print = h_change_minutes_to_hours(average_time_spent)
                text_to_print = text_to_print + "Die meiste Zeit ingesamt (" + most_time_spent_on_material_print + ") wurde mit der Lernaufgabe " + material_most_time_spent_on + " verbracht. Im Durchschnitt waren es " + average_time_spent_print + ". "
            
            if h_test_if_im(material_most_time_spent_on):
                average_time_spent = h_get_average_time_spent_on_im(material_most_time_spent_on)
                average_time_spent_print = h_change_minutes_to_hours(average_time_spent)
                text_to_print = text_to_print + "Die meiste Zeit ingesamt (" + most_time_spent_on_material_print + ") wurde mit der Informationsseite " + material_most_time_spent_on + " verbracht. Im Durchschnitt waren es " + average_time_spent_print + ". "
            
        if least_time_spent:
            least_time_spent_on_material = least_time_spent[0]['Gesamtzeit']
            least_time_spent_on_material_print = h_change_minutes_to_hours(least_time_spent_on_material)
            material_least_time_spent_on = least_time_spent[0]['Material']

            if h_test_if_task(material_least_time_spent_on):
                average_time_spent = h_get_average_time_spent_on_task(material_least_time_spent_on)
                average_time_spent_print = h_change_minutes_to_hours(average_time_spent)
                text_to_print = text_to_print + "Die wenigste Zeit ingesamt (" + least_time_spent_on_material_print + ") wurde mit der Lernaufgabe " + material_least_time_spent_on + " verbracht. Im Durchschnitt waren es " + average_time_spent_print + ". "
            
            if h_test_if_im(material_least_time_spent_on):
                average_time_spent = h_get_average_time_spent_on_im(material_least_time_spent_on)
                average_time_spent_print = h_change_minutes_to_hours(average_time_spent)
                text_to_print = text_to_print + "Die wenigste Zeit ingesamt (" + least_time_spent_on_material_print + ") wurde mit der Informationsseite " + material_least_time_spent_on + " verbracht. Im Durchschnitt waren es " + average_time_spent_print + ".\n "

        if not_visited and not_visited[0]['Material'] is not None:
            not_visited_list = []
            for record in not_visited: 
                not_visited_list.append(record['Material'])
            text_to_print = text_to_print + "Die folgenden Seiten wurden gar nicht besucht: " + (", ".join(not_visited_list)) + ". "
        else:
            text_to_print = text_to_print + "Es gibt keine Seiten, die gar nicht besucht wurden. "

        print(text_to_print)
        text_to_print = "Was die Elemente des Frameworks Data Science angeht, so wurde für die folgenden Kompetenzen, Wissensbausteine und Fähigkeiten die meiste Zeit aufgewendet:\n"
        time_spent_on_competences_knowledge_skills = get_practice_of_competence_knowledge_skill()
        text_to_print = text_to_print + time_spent_on_competences_knowledge_skills
        
        print(text_to_print)

    except Neo4jError as e:
        print("In der Funktion zur Ausgabe von Informationen zur im Kurs verbrachten Zeit ist leider ein Neo4j-Fehler aufgetreten.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)

# gibt allgemeine Informationen zum Kurs, darunter auch schon den Inhalt von print_information_on_difficult_tasks (Informationen zu augenscheinlich schwierigen Aufgaben)
# und print_information_on_time_spent_in_course (Informationen zur Verteilung der im Kurs verbrachten Zeit) aus
def print_general_information_on_course():
    try:
        with driver.session() as session:
            number_of_fully_completed_tasks = session.run("""
                MATCH (s:Student)
                WITH COUNT(s) AS ZahlStudierende
                MATCH (t: Student)-[c:completed]->(lt:Learning_Task)
                WITH ZahlStudierende, lt.title AS Aufgabe, COUNT(t) AS AnzahlStudierenderAbgeschlossen
                WHERE AnzahlStudierenderAbgeschlossen = ZahlStudierende
                RETURN COUNT(Aufgabe) AS ZahlKomplettAbgeschlossenerAufgaben""").data()
            number_of_tasks_with_full_number_of_attempts = session.run("""
                MATCH (s:Student)
                WITH COUNT(s) AS ZahlStudierende
                MATCH (t: Student)-[r:struggled_with|successfully_solved]->(lt:Learning_Task)
                WITH ZahlStudierende, lt.title AS Aufgabe, COUNT(DISTINCT t) AS ZahlStudierendeMitVersuchen
                WHERE ZahlStudierendeMitVersuchen = ZahlStudierende
                RETURN COUNT(Aufgabe) AS AnzahlAufgabenAlleGelöst""").data()
            total_number_of_attempts = session.run("""
                MATCH ()-[r:struggled_with|successfully_solved]->(lt:Learning_Task)
                RETURN COUNT(r) AS GesamtzahlVersuche""").data()
            most_attempts_for_task = session.run("""
                MATCH ()-[r:struggled_with|successfully_solved]->(lt:Learning_Task)
                WITH lt.title AS Aufgabe, COUNT(r) AS GesamtzahlVersucheProAufgabe
                WITH max(GesamtzahlVersucheProAufgabe) AS maxZahl
                MATCH ()-[r:struggled_with|successfully_solved]->(lt:Learning_Task)
                WITH lt.title AS Aufgabe, COUNT(r) AS GesamtzahlVersucheProAufgabe, maxZahl
                WHERE GesamtzahlVersucheProAufgabe = maxZahl
                RETURN Aufgabe, GesamtzahlVersucheProAufgabe""").data()
            least_attempts_for_task = session.run("""
                MATCH ()-[r:struggled_with|successfully_solved]->(lt:Learning_Task)
                WITH lt.title AS Aufgabe, COUNT(r) AS GesamtzahlVersucheProAufgabe
                WITH min(GesamtzahlVersucheProAufgabe) AS minZahl
                MATCH ()-[r:struggled_with|successfully_solved]->(lt:Learning_Task)
                WITH lt.title AS Aufgabe, COUNT(r) AS GesamtzahlVersucheProAufgabe, minZahl
                WHERE GesamtzahlVersucheProAufgabe = minZahl
                RETURN Aufgabe, GesamtzahlVersucheProAufgabe """).data()
            most_successful_attempts_for_task = session.run("""
                MATCH ()-[r:successfully_solved]->(lt:Learning_Task)
                WITH lt.title AS Aufgabe, COUNT(r) AS GesamtzahlVersucheProAufgabe
                WITH max(GesamtzahlVersucheProAufgabe) AS maxZahl
                MATCH ()-[r:successfully_solved]->(lt:Learning_Task)
                WITH lt.title AS Aufgabe, COUNT(r) AS GesamtzahlVersucheProAufgabe, maxZahl
                WHERE GesamtzahlVersucheProAufgabe = maxZahl
                RETURN Aufgabe, GesamtzahlVersucheProAufgabe """).data()
            best_result_altogether = session.run("""
                MATCH()-[r:successfully_solved|struggled_with]->(lt:Learning_Task)
                WITH lt.title AS Aufgabe, AVG(r.score) AS Durchschnittsergebnis
                WITH max(Durchschnittsergebnis) AS maxZahl
                MATCH()-[r:successfully_solved|struggled_with]->(lt:Learning_Task)
                WITH lt.title AS Aufgabe, AVG(r.score) AS Durchschnittsergebnis, maxZahl
                WHERE Durchschnittsergebnis = maxZahl
                RETURN Aufgabe, Durchschnittsergebnis""").data()
            average_result_all_tasks = session.run("""
                MATCH()-[r:successfully_solved|struggled_with]->()
                WITH AVG(r.score) AS Durchschnittsergebnis
                RETURN Durchschnittsergebnis""").data()
            number_of_fully_completed_pi = session.run("""
                MATCH (s:Student)
                WITH COUNT(s) AS ZahlStudierende
                MATCH (t: Student)-[c:completed]->(pi: Procedural_Information)
                WITH ZahlStudierende, pi.title AS PI, COUNT(DISTINCT t) AS AnzahlStudierenderAbgeschlossen
                WHERE AnzahlStudierenderAbgeschlossen = ZahlStudierende
                RETURN COUNT(PI) AS ZahlKomplettAbgeschlossenePI""").data()
            number_of_covered_pi = session.run("""
                MATCH (s:Student)
                WITH COUNT(s) AS ZahlStudierende
                MATCH (t: Student)-[]->(ls:Learning_Session)-[c:covered]->(pi: Procedural_Information)
                WITH ZahlStudierende, pi.title AS PI, COUNT(DISTINCT t) AS AnzahlStudierenderBesucht
                WHERE AnzahlStudierenderBesucht = ZahlStudierende
                RETURN COUNT(PI) AS ZahlVonAllenBesuchtePI""").data()
            number_of_fully_completed_si = session.run("""
                MATCH (s:Student)
                WITH COUNT(s) AS ZahlStudierende
                MATCH (t: Student)-[c:completed]->(si: Supportive_Information)
                WITH ZahlStudierende, si.title AS SI, COUNT(DISTINCT t) AS AnzahlStudierenderAbgeschlossen
                WHERE AnzahlStudierenderAbgeschlossen = ZahlStudierende
                RETURN COUNT(SI) AS ZahlKomplettAbgeschlosseneSI""").data()
            number_of_covered_si = session.run("""
                MATCH (s:Student)
                WITH COUNT(s) AS ZahlStudierende
                MATCH (t: Student)-[]->(ls:Learning_Session)-[c:covered]->(si: Supportive_Information)
                WITH ZahlStudierende, si.title AS SI, COUNT(DISTINCT t) AS AnzahlStudierenderBesucht
                WHERE AnzahlStudierenderBesucht = ZahlStudierende
                RETURN COUNT(SI) AS ZahlVonAllenBesuchteSI""").data()

            print_information_on_time_spent_in_course() 

            number_of_learning_tasks = h_get_number_of_learning_tasks()
            if number_of_fully_completed_tasks and number_of_fully_completed_tasks[0]['ZahlKomplettAbgeschlossenerAufgaben'] is not None:
                number_of_fully_completed_tasks = number_of_fully_completed_tasks[0]['ZahlKomplettAbgeschlossenerAufgaben']
                percentage_of_fully_completed_tasks = round(number_of_fully_completed_tasks / number_of_learning_tasks * 100)
                print("Von den " + str(number_of_learning_tasks) + " Lernaufgaben im Kurs wurden " + str(percentage_of_fully_completed_tasks) + " Prozent von allen Studierenden abgeschlossen (durch einen Lösungsversuch oder den \"Mark as done\"-Button)." )
            
            if number_of_tasks_with_full_number_of_attempts and number_of_tasks_with_full_number_of_attempts[0]['AnzahlAufgabenAlleGelöst'] is not None:
                number_of_tasks_with_full_number_of_attempts = number_of_tasks_with_full_number_of_attempts[0]['AnzahlAufgabenAlleGelöst']
                percentage_of_tasks_with_full_number_of_attempts = round(number_of_tasks_with_full_number_of_attempts/number_of_learning_tasks *100)
                print("Zu " + str(percentage_of_tasks_with_full_number_of_attempts) + " Prozent der Aufgaben haben alle Studierenden mindestens einen Lösungsversuch abgegeben.")

            if total_number_of_attempts and total_number_of_attempts[0]['GesamtzahlVersuche'] is not None:
                print("Insgesamt wurden zu den " + str(number_of_learning_tasks) + " Lernaufgaben im Kurs " + str(total_number_of_attempts[0]['GesamtzahlVersuche']) + " Lösungsversuche abgegeben. ")

            if most_attempts_for_task:
                most_attempts_task_list = []
                number_of_attempts_most = most_attempts_for_task[0]['GesamtzahlVersucheProAufgabe']
                for record in most_attempts_for_task:
                    most_attempts_task_list.append(record['Aufgabe'])
                print("Die meisten Lösungsversuche (" + str(number_of_attempts_most) + ") gab es bei " + (", ".join(most_attempts_task_list)) + ". ")
            
            if least_attempts_for_task:
                least_attempts_task_list = []
                number_of_attempts_least = least_attempts_for_task[0]['GesamtzahlVersucheProAufgabe']
                for record in least_attempts_for_task:
                    least_attempts_task_list.append(record['Aufgabe'])
                print("Die wenigsten Lösungsversuche (" + str(number_of_attempts_least) + ") gab es bei " + (", ".join(least_attempts_task_list)) + ".\n")

            if most_successful_attempts_for_task:
                most_successful_attempts_for_task_list = []
                most_successful_attempts_number = most_successful_attempts_for_task[0]['GesamtzahlVersucheProAufgabe']
                for record in most_successful_attempts_for_task:
                    most_successful_attempts_for_task_list.append(record['Aufgabe'])
                print("Die meisten erfolgreichen Lösungsversuche, das heißt Versuche mit mehr als 80 Prozent der Punkte (" + str(most_successful_attempts_number) + ") gab es bei " + (", ".join(most_successful_attempts_for_task_list)) + ".\n")


            print_information_on_difficult_tasks()

            if best_result_altogether:
                best_result_tasks_list = []
                best_result_altogether_score = best_result_altogether[0]['Durchschnittsergebnis']
                for record in best_result_altogether:
                    best_result_tasks_list.append(record['Aufgabe'])
                print("Das beste Durchschnittsergebnis wurde mit " + str(best_result_altogether_score) + " Punkten bei " + (", ".join(best_result_tasks_list)) + " erzielt. ")

            if average_result_all_tasks and average_result_all_tasks[0]['Durchschnittsergebnis'] is not None:
                print("Insgesamt wurden über den ganzen Kurs hinweg unter Betrachtung aller Aufgaben durchschnittlich " + str(round(average_result_all_tasks[0]['Durchschnittsergebnis'],2)) + " Punkte pro Aufgabe erzielt.")

            number_of_pi = h_get_number_of_pi()
            if number_of_fully_completed_pi and number_of_fully_completed_pi[0]['ZahlKomplettAbgeschlossenePI'] is not None:
                number_of_fully_completed_pi = number_of_fully_completed_pi[0]['ZahlKomplettAbgeschlossenePI']
                percentage_of_fully_completed_pi = round(number_of_fully_completed_pi / number_of_pi * 100)
                print("Von den " + str(number_of_pi) + " Procedural Information-Seiten im Kurs wurden " + str(percentage_of_fully_completed_pi) + " Prozent von allen Studierenden als abgeschlossen markiert. ")
            if number_of_covered_pi and number_of_covered_pi[0]['ZahlVonAllenBesuchtePI'] is not None:
                number_of_covered_pi = number_of_covered_pi[0]['ZahlVonAllenBesuchtePI']
                percentage_of_covered_pi = round(number_of_covered_pi / number_of_pi * 100)
                print(str(percentage_of_covered_pi) + " Prozent wurden von allen Studierenden mindestens einmal aufgerufen.")

            number_of_si = h_get_number_of_si()
            if number_of_fully_completed_si and number_of_fully_completed_si[0]['ZahlKomplettAbgeschlosseneSI'] is not None:
                number_of_fully_completed_si = number_of_fully_completed_si[0]['ZahlKomplettAbgeschlosseneSI']
                percentage_of_fully_completed_si = round(number_of_fully_completed_si / number_of_si * 100)
                print("Von den " + str(number_of_si) + " Supportive Information-Seiten im Kurs wurden " + str(percentage_of_fully_completed_si) + " Prozent von allen Studierenden als abgeschlossen markiert. ")
            if number_of_covered_si and number_of_covered_si[0]['ZahlVonAllenBesuchteSI'] is not None:
                number_of_covered_si = number_of_covered_si[0]['ZahlVonAllenBesuchteSI']
                percentage_of_covered_si = round(number_of_covered_si / number_of_si * 100)
                print(str(percentage_of_covered_si) + " Prozent wurden von allen Studierenden mindestens einmal aufgerufen.")

            return

    except Neo4jError as e:
        print("In der Funktion zur Ausgabe von generellen Informationen zum Kurs ist leider ein Neo4j-Fehler aufgetreten.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return

# nutzt einen Similarity-Algorithmus, um ähnliche Lernprofile zu finden - in einem ersten Schritt in Bezug auf die erreichten Punktzahlen (ähnliche Wissensprofile), in
# einem zweiten Schritt in Bezug auf die mit Lernmaterial (Aufgaben und Informationsmaterial) verbrachte Zeit.
def print_information_on_similar_learning_profiles():
    try:
        with driver.session() as session:
            # Projektion erstellen, in der Studierenden-Knoten mit den bearbeiteten Aufgabenknoten verbunden werden und in der die erzielten Punktzahlen die Kantengewichte sind
            session.run("""
                CALL gds.graph.drop('student-tasks', false)
                YIELD graphName""")
            session.run("""
                MATCH (source:Student)
                OPTIONAL MATCH (source)-[r:successfully_solved|struggled_with]->(target: Learning_Task)
                RETURN gds.graph.project(
                    'student-tasks',
                    source,
                    target,
                    {sourceNodeLabels: labels(source),
                    targetNodeLabels: labels(target),
                    relationshipType: type(r),
                    relationshipProperties: r {.score}},
                    {})""")
            # Similarity-Algorithmus auf der Projektion laufen lassen
            similar_profiles_points = session.run("""
                CALL gds.nodeSimilarity.stream(
                    'student-tasks',
                    {relationshipWeightProperty: 'score',
                    similarityCutoff: 0.5})
                YIELD node1, node2, similarity
                WHERE node1 < node2
                RETURN gds.util.asNode(node1).last_name AS Student1, gds.util.asNode(node2).last_name AS Student2, similarity AS Ähnlichkeit ORDER BY Ähnlichkeit DESC, Student1, Student2""").data()
            # Projektion erstellen, in der Studierenden-Knoten mit den bearbeiteten Materialien verbunden werden und in der die damit verbrachte Zeit als Kantengewicht genutzt wird
            session.run("""
                CALL gds.graph.drop('student-time-spent', false)
                YIELD graphName""")
            session.run("""
                MATCH (source:Student)
                OPTIONAL MATCH (source)-[:did_learning_session]->(:Learning_Session)-[r:covered]->(target)
                RETURN gds.graph.project(
                    'student-time-spent',
                    source,
                    target,
                    {sourceNodeLabels: labels(source),
                    targetNodeLabels: labels(target),
                    relationshipType: type(r),
                    relationshipProperties: r {.time_spent}},
                    {})""")
            # Similarity-Algorithmus auf der Projektion laufen lassen
            similar_profiles_time = session.run("""
                CALL gds.nodeSimilarity.stream(
                    'student-time-spent',
                    {relationshipWeightProperty: 'time_spent',
                    similarityCutoff: 0.5})
                YIELD node1, node2, similarity
                WHERE node1 < node2
                RETURN gds.util.asNode(node1).last_name AS Student1, gds.util.asNode(node2).last_name AS Student2, similarity AS Ähnlichkeit ORDER BY Ähnlichkeit DESC, Student1, Student2""").data()

            if similar_profiles_points:
                print("Es wurde nach ähnlichen Wissensprofilen bei Studierenden basierend auf der Verteilung der bei den Aufgaben erreichten Punkte gesucht. Die folgenden Studierenden-Paare wiesen hierbei die höchsten Ähnlichkeitswerte auf:\n ")
                for i in range(len(similar_profiles_points)):
                    if similar_profiles_points[i]['Student1'] is not None and similar_profiles_points[i]['Student2'] is not None:
                        print("- Herr/Frau " + str(similar_profiles_points[i]['Student1']) + " und Herr/Frau " + str(similar_profiles_points[i]['Student2']) + " (" + str(round(similar_profiles_points[i]["Ähnlichkeit"],2)) + ")\n")
            else:
                print("Es wurde nach ähnlichen Wissensprofilen bei Studierenden basierend auf der Verteilung der bei den Aufgaben erreichten Punkte gesucht. Es gab jedoch keine Studierenden-Paare, die Ähnlichkeitswerte größer als 0,5 aufwiesen.\n")
        
            if similar_profiles_time:
                print("Darüber hinaus wurde nach Ähnlichkeiten in Bezug auf die mit Lernmaterial (Aufgaben und Informationsmaterial) verbrachte Zeit gesucht. Die folgenden Studierenden-Paare wiesen hierbei die höchsten Ähnlichkeitswerte auf:\n ")
                for i in range(len(similar_profiles_time)):
                    if similar_profiles_time[i]['Student1'] is not None and similar_profiles_time[i]['Student2'] is not None:
                        print("- Herr/Frau " + str(similar_profiles_time[i]['Student1']) + " und Herr/Frau " + str(similar_profiles_time[i]['Student2']) + " (" + str(round(similar_profiles_time[i]["Ähnlichkeit"],2)) + ")\n")
            else:
                print("Darüber hinaus wurde nach Ähnlichkeiten in Bezug auf die mit Lernmaterial (Aufgaben und Informationsmaterial) verbrachte Zeit gesucht. Hier gab es jedoch keine Studierenden-Paare, die Ähnlichkeitswerte größer als 0,5 aufwiesen.\n") 
            
        driver.execute_query("""
            CALL gds.graph.drop('student-tasks', false)
            YIELD graphName""")
        driver.execute_query("""
            CALL gds.graph.drop('student-time-spent', false)
            YIELD graphName""")

    except Neo4jError as e:
        print("In der Funktion zur Ermittlung von ähnlichen Lernprofilen ist leider ein Neo4j-Fehler aufgetreten.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return

# nutzt einen Clustering-Algorithmus, um oft zusammen bearbeitete Lerninhalte (Aufgaben und Informationsmaterial) zu finden.
def print_information_on_related_material():
    try:
        with driver.session() as session:
            # Projektion erstellen, in der in mindestens einer Learning Session zusammen bearbeitete Inhalte über eine ungerichtete Relation verbunden sind und in der die Anzahl der gemeinsamen
            # Learning Sessions die Kantengewichte bildet
            session.run("""
                CALL gds.graph.drop('material-clusters', false)
                YIELD graphName""")
            session.run("""
                MATCH(source:Learning_Task|Information_Material)<-[r:covered]-(:Learning_Session)-[:covered]->(target:Learning_Task|Information_Material)
                WITH source, target, COUNT(r) AS numberOfCommonSessions
                RETURN gds.graph.project(
                    'material-clusters',
                    source,
                    target,
                    {relationshipProperties: {commonSessions: numberOfCommonSessions}},
                    {undirectedRelationshipTypes: ['*']})""")
            # Leiden-Algorithmus zur Community Detection auf der Projektion laufen lassen
            material_communities = session.run("""
                CALL gds.leiden.stream(
                    'material-clusters',
                    {relationshipWeightProperty: 'commonSessions'}
                )
                YIELD nodeId, communityId
                RETURN gds.util.asNode(nodeId).title AS Material, communityId AS CommunityID ORDER BY CommunityID, Material
                """).data()
            
            if material_communities and material_communities[0]['CommunityID'] is not None:
                print("Es wurde analysiert, welche Lernmaterialien oft zusammen bearbeitet wurden. ")
                communityId = material_communities[0]['CommunityID']
                list = []
                i = 1
                for row in material_communities:
                    if row['CommunityID']==communityId:
                        list.append(row['Material'])
                    else:
                        result_list = ", ".join(list)
                        print("- Gruppe  " + str(i) + ": " + result_list + "\n")
                        i = i+1
                        list = []
                        communityId = row['CommunityID']
                        list.append(row['Material'])
                
                result_list = ", ".join(list)
                print("- Gruppe  " + str(i) + ": " + result_list + "\n")
        
        driver.execute_query("""
                CALL gds.graph.drop('material-clusters', false)
                YIELD graphName""")

    except Neo4jError as e:
        print("In der Funktion zur Ermittlung oft zusammen bearbeitetem Lernmaterial ist leider ein Neo4j-Fehler aufgetreten.")
        print("Neo4j error code: " + str(e.code))
        if e.message is not None:
            print("Exception message: " + e.message)
        return


def main():
    parser = argparse.ArgumentParser(description="Grundlegende Abfragefunktionen für die im Graphen gespeicherten Lernverhaltensdaten")
    
    subparsers = parser.add_subparsers(dest='funktion', required=True)

    subparsers.add_parser('print_general_information_on_course', help="Allgemeine Informationen zum Kurs abfragen" )

    subparsers.add_parser('print_information_on_related_material', help="Informationen zu oft zusammen bearbeitetem Material abfragen" )
    subparsers.add_parser('print_information_on_similar_learning_profiles', help="Informationen zu ähnlichen Lernprofilen abfragen")
    subparsers.add_parser('print_information_on_difficult_tasks', help="Informationen zu schwierigen Aufgaben abfragen" )
    subparsers.add_parser('print_information_on_success_in_course', help="Informationen zu besonders erfolgreichen Studierenden abfragen" )
    subparsers.add_parser('print_information_on_time_spent_in_course', help="Informationen zur im Kurs verbrachten Zeit abfragen" )
    subparsers.add_parser('print_difficulties_with_skills', help="Informationen Schwierigkeiten mit Fähigkeiten abfragen" )
    subparsers.add_parser('print_difficulties_with_knowledge_items', help="Informationen Schwierigkeiten mit Wissensbausteinen abfragen" )
    subparsers.add_parser('print_difficulties_with_competences', help="Informationen Schwierigkeiten mit Kompetenzen abfragen" )

    parser_general_info_student = subparsers.add_parser('print_general_information_on_student', help="Allgemeine Informationen über einen Studierenden abfragen")
    parser_general_info_student.add_argument('student_name', type=str, help="Nachnamen des Studierenden eingeben")

    parser_content_sessions = subparsers.add_parser('print_content_of_learning_sessions', help="Inhalte der Lernsitzungen eines Studierenden abfragen")
    parser_content_sessions.add_argument('student_name', type=str, help="Nachnamen des Studierenden eingeben")

    parser_order = subparsers.add_parser('print_learning_order_of_student_everything', help="Bearbeitungsreihenfolge eines Studierenden abfragen")
    parser_order.add_argument('student_name', type=str, help="Nachnamen des Studierenden eingeben")

    parser_difficult_tasks_for_student = subparsers.add_parser('print_information_on_difficult_tasks_for_student', help="Schwierigkeiten mit Aufgaben eines Studierenden abfragen")
    parser_difficult_tasks_for_student.add_argument('student_name', type=str, help="Nachnamen des Studierenden eingeben")

    parser_performance_task = subparsers.add_parser('print_information_on_students_performance_with_task', help="Informationen zu einem Studierenden und einer Aufgabe abfragen")
    parser_performance_task.add_argument('student_name', type=str, help="Nachnamen des Studierenden eingeben")
    parser_performance_task.add_argument('task_name', type=str, help="Namen der Aufgabe eingeben")

    parser_lp_skill = subparsers.add_parser('print_last_practice_of_skill', help="Letzte Beschäftigung eines Studierenden mit einer Fähigkeit abfragen")
    parser_lp_skill.add_argument('student_name', type=str, help="Nachnamen des Studierenden eingeben")
    parser_lp_skill.add_argument('skill_name', type=str, help="Namen der Fähigkeit eingeben")

    parser_lp_knowledge = subparsers.add_parser('print_last_practice_of_knowledge', help="Letzte Beschäftigung eines Studierenden mit einem Wissenselement abfragen")
    parser_lp_knowledge.add_argument('student_name', type=str, help="Nachnamen des Studierenden eingeben")
    parser_lp_knowledge.add_argument('knowledge_name', type=str, help="Namen des Wissenselements eingeben")

    parser_lp_competence = subparsers.add_parser('print_last_practice_of_competence', help="Letzte Beschäftigung eines Studierenden mit einer Kompetenz abfragen")
    parser_lp_competence.add_argument('student_name', type=str, help="Nachnamen des Studierenden eingeben")
    parser_lp_competence.add_argument('competence_name', type=str, help="Namen der Kompetenz eingeben")

    parser_skill_id = subparsers.add_parser('print_general_information_on_skill_from_id', help="Allgemeine Informationen zu einer Fähigkeit abfragen")
    parser_skill_id.add_argument('skill_id', type=str, help="ID der Fähigkeit eingeben")

    parser_skill_name = subparsers.add_parser('print_general_information_on_skill_from_name', help="Allgemeine Informationen zu einer Fähigkeit abfragen")
    parser_skill_name.add_argument('skill_name', type=str, help="Namen der Fähigkeit eingeben")

    parser_knowledge_id = subparsers.add_parser('print_general_information_on_knowledge_from_id', help="Allgemeine Informationen zu einem Wissenslement abfragen")
    parser_knowledge_id.add_argument('knowledge_id', type=str, help="ID des Wissenselements eingeben")

    parser_knowledge_name = subparsers.add_parser('print_general_information_on_knowledge_from_name', help="Allgemeine Informationen zu einem Wissenselement abfragen")
    parser_knowledge_name.add_argument('knowledge_name', type=str, help="Namen des Wissenselements eingeben")

    parser_competence_id = subparsers.add_parser('print_general_information_on_competence_from_id', help="Allgemeine Informationen zu einer Kompetenz abfragen")
    parser_competence_id.add_argument('competence_id', type=str, help="ID der Kompetenz eingeben")

    parser_competence_name = subparsers.add_parser('print_general_information_on_competence_from_name', help="Allgemeine Informationen zu einer Kompetenz abfragen")
    parser_competence_name.add_argument('competence_name', type=str, help="Namen der Kompetenz eingeben")

    parser_general_info_task = subparsers.add_parser('print_general_information_on_task', help="Allgemeine Informationen zu einer Aufgabe abfragen")
    parser_general_info_task.add_argument('task_name', type=str, help="Namen der Aufgabe eingeben")

    parser_general_info_im = subparsers.add_parser('print_general_information_on_information_material', help="Allgemeine Informationen zu einer Aufgabe abfragen")
    parser_general_info_im.add_argument('im_name', type=str, help="Namen der Informationsseite eingeben")
    
    sys.argv = ["neo4j_analytics.py", "print_general_information_on_course"]
    args = parser.parse_args()

    if args.funktion == 'print_general_information_on_course':
        print_general_information_on_course()
    elif args.funktion == 'print_information_on_related_material':
        print_information_on_related_material()
    elif args.funktion == 'print_information_on_similar_learning_profiles':
        print_information_on_similar_learning_profiles()
    elif args.funktion == 'print_general_information_on_student':
        print_general_information_on_student(args.student_name)
    elif args.funktion == 'print_content_of_learning_sessions':
        print_content_of_learning_sessions(args.student_name)
    elif args.funktion == 'print_learning_order_of_student_everything':
        print_learning_order_of_student_everything(args.student_name)
    elif args.funktion == 'print_information_on_difficult_tasks_for_student':
        print_information_on_difficult_tasks_for_student(args.student_name)
    elif args.funktion == 'print_information_on_students_performance_with_task':
        print_information_on_students_performance_with_task(args.student_name, args.task_name)
    elif args.funktion == 'print_last_practice_of_skill':
        print_last_practice_of_skill(args.student_name, args.skill_name)
    elif args.funktion == 'print_last_practice_of_knowledge':
        print_last_practice_of_knowledge(args.student_name, args.knowledge_name)
    elif args.funktion == 'print_last_practice_of_competence':
        print_last_practice_of_competence(args.student_name, args.competence_name)
    elif args.funktion == 'print_general_information_on_skill_from_id':
        print_general_information_on_skill_from_id(args.skill_id) 
    elif args.funktion == 'print_general_information_on_skill_from_name':
        print_general_information_on_skill_from_name(args.skill_name) 
    elif args.funktion == 'print_general_information_on_knowledge_from_id':
        print_general_information_on_knowledge_from_id(args.knowledge_id) 
    elif args.funktion == 'print_general_information_on_knowledge_from_name':
        print_general_information_on_knowledge_from_name(args.knowledge_name) 
    elif args.funktion == 'print_general_information_on_competence_from_id':
        print_general_information_on_competence_from_id(args.competence_id) 
    elif args.funktion == 'print_general_information_on_competence_from_name':
        print_general_information_on_competence_from_name(args.competence_name)
    elif args.funktion == 'print_difficulties_with_skills':
        print_difficulties_with_skills()
    elif args.funktion == 'print_difficulties_with_knowledge_items': 
        print_difficulties_with_knowledge_items()
    elif args.funktion == 'print_difficulties_with_competences':
        print_difficulties_with_competences() 
    elif args.funktion == 'print_general_information_on_task':
        print_general_information_on_task(args.task_name) 
    elif args.funktion == 'print_general_information_on_information_material':
        print_general_information_on_information_material(args.im_name)
    elif args.funktion == 'print_information_on_difficult_tasks':
        print_information_on_difficult_tasks() 
    elif args.funktion == 'print_information_on_success_in_course':
        print_information_on_success_in_course()
    elif args.funktion == 'print_information_on_time_spent_in_course':
        print_information_on_time_spent_in_course() 



if __name__ == "__main__":
    main()