import sqlite3     # For SQLite database interaction
import requests    # For making HTTP requests
import json        # For handling JSON data
import os          # For interacting with the operating system
import time        # For time-related functionality
import webbrowser  # For opening web browser from the script
import datetime    # For date and time-related functionality
from typing import List, Dict, Union, Tuple  # For type hinting

# Typing
KeyType = Dict[str, str]  # Data Type for API Key, dictionary where both keys and values are strings.
DataType = List[Dict[str, Union[str, int]]]  # Data Type for retrieved data, type is a list of dictionaries
                                             # with string keys and values that can be either strings or integers.
class Trainer:
    '''
    SmokiFit Guide - Your Personal Fitness Companion.

    This class handles the virtual fitness trainer functionalities.

    Attributes:
    - difficulty: Difficulty level for exercise search.
    - type: Exercise type for search.
    - muscle: Muscle targeted for exercise search.
    - name: Name of the exercise for named search.
    - food: Name of the food for nutrition search.
    - mode: Current mode of operation (exercise/nutrition).
    - key: API key used for making requests.
    '''
    def __init__(self):
        '''Initialize the Trainer class with default values.'''
        self.difficulty = ''
        self.type = ''
        self.muscle = ''
        self.name = ''
        self.food = ''
        self.mode = ''
        self.key: KeyType = self.load_key()

    def load_key(self) -> KeyType:
        '''Checks if a config file exists, loads the API key from it, verifies its validity, or prompts the user for a new key if needed.'''
        if os.path.exists('config.txt'):
            with open('config.txt', 'r') as config_file:
                data = json.load(config_file)
                key = data.get('key', '')
            verify = self.verify_key(key)
            if verify[0]:
                print("Lighten up your mood buddy.", verify[1])
                return {'X-Api-Key': key}
            else:
                print("Your API key has expired. Please set a valid key.")
                print("Free API key at \033[4mhttps://api-ninjas.com\033[0m.")
                return self.ask_for_key()
        else:
            self.introduction()
            return self.ask_for_key()

    def introduction(self) -> None:
        '''Displays a welcoming introduction and instructions to the user.'''
        print("Welcome to SmokiFit Guide - Your Personal Fitness Companion!")
        # sleep() is used to simulate loading
        time.sleep(1)
        print("\nHello there! I'm Smoki, your virtual fitness trainer. Whether you're looking for tailored exercises or nutritional information, I'm here to guide you on your wellness journey. Before we dive in, let me give you a quick overview and some instructions.")
        time.sleep(2)
        print("\nSmokiFit Guide allows you to explore a variety of exercises and nutrition facts. You can search for exercises based on difficulty, type, and muscle, or discover nutritional details for different foods.")
        time.sleep(2)
        input("\nBefore we begin, you'll need to provide an API key. Don't worry; it's easy! Visit \033[4mhttps://api-ninjas.com\033[0m to get your free API key. Once you have it, enter it below, and I will remember it for future sessions. Press enter to get redirected to website.")
        # Open the website in default browser from the console.
        webbrowser.open("https://api-ninjas.com")
        
    def ask_for_key(self) -> KeyType:
        '''Interacts with the user to enter the API key, verifies its validity and Returns it.'''
        while True:
            key = input("Enter your API key: ").strip()
            if key.lower() == 'cancel':
                break
            verify = self.verify_key(key)
            if verify[0]:
                self.save_key(key)
                print("\nAPI key has been set.")
                print("\nWanna listen to a joke?", verify[1])
                return {'X-Api-Key': key}
            else:
                print("Invalid API key. Please try again.")
    
    def verify_key(self, key: str) -> Tuple[bool, str]:
        '''
        Checks if the provided API key is valid by making a request to the API.

        Args:
        - key (str): API key to be verified.

        Returns:
        - tuple: A tuple containing a boolean indicating verification status and a joke if valid.
        '''
        headers = {'X-Api-Key': key}
        response = requests.get('https://api.api-ninjas.com/v1/dadjokes?limit=1', headers=headers)
        if response.status_code == requests.codes.ok:
            return (True, json.loads(response.text)[0]['joke'])
        else:
            return (False,)
    
    def save_key(self, key: str) -> None:
        '''
        Stores the API key in a configuration file for future sessions.

        Arg:
        - key (str): API key to be saved.
        '''
        data = {'key': key}
        with open('config.txt', 'w') as config_file:
            json.dump(data, config_file)

    def get_data(self) -> str:
        '''
        Makes a request to the API to retrieve data based on the current mode and parameters.

        Returns:
        - str: Response text from the API.
        '''
        if self.mode == 'exercise':
            api_url = 'https://api.api-ninjas.com/v1/exercises?difficulty={0}&type={1}&muscle={2}&name={3}'.format(self.difficulty, self.type, self.muscle, self.name)
        elif self.mode == 'nutrition':
            api_url = 'https://api.api-ninjas.com/v1/nutrition?query={}'.format(self.food)
        
        response = requests.get(api_url, headers=self.key)
        
        if response.status_code == requests.codes.ok:
            self.difficulty = self.type = self.muscle = self.name = self.food = ''
            return response.text
        else:
            print("Error:", response.status_code, response.text)

class UserData:
    def __init__(self):
        '''Initialize the UserData object, connecting to the SQLite database, creating necessary tables, and initializing the user\'s daily calories intake goal.'''
        self.conn = sqlite3.connect(f'user_data.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS SavedExercises (
                ExerciseName TEXT PRIMARY KEY,
                ExerciseDetails TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS SearchedFoodHistory (
                FoodDetails TEXT
            )
        ''')
        # Try to load the previous day’s goal.
        try:
            self.cursor.execute('SELECT Goal, Date FROM DailyCalories ORDER BY Date DESC')
            data = self.cursor.fetchone()
            self.goal = data[0]
            # Create a record for today if it doesn't exist already.
            if data[1] != datetime.datetime.now().strftime('%Y-%m-%d'):
                self.cursor.execute('''
                    INSERT INTO DailyCalories (Date, Consumed, Goal) VALUES (?, ?, ?)
                ''', (datetime.datetime.now().strftime('%Y-%m-%d'), 0, self.goal))
                
                # Keep only the last 7 days of history to avoid redundancy.
                self.cursor.execute('''
                    DELETE FROM DailyCalories 
                    WHERE Date NOT IN (
                        SELECT Date FROM DailyCalories ORDER BY Date DESC LIMIT 7
                    )
                ''')
                self.conn.commit()

        # In the first run, there will be an OperationalError, meaning the table doesn't exist, so create it, prompt the user to set a daily calories intake goal and enter the first record with today's date.
        except sqlite3.OperationalError:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS DailyCalories (
                    Date TEXT PRIMARY KEY,
                    Consumed INTEGER DEFAULT 0,
                    Goal INTEGER
                )
            ''')
            goal = int(input("\nEnter your daily calories intake goal: "))
            self.cursor.execute('''
            INSERT INTO DailyCalories (Date, Consumed, Goal) VALUES (?, ?, ?)
            ''', (datetime.datetime.now().strftime('%Y-%m-%d'), 0, goal))
            self.conn.commit()
            self.goal = goal

    def config_calories_goal(self, goal: int) -> None:
        '''
        Changes the daily calories intake goal to the provided new goal.
        
        Args:
        - goal (int): New daily calories intake goal.
        '''
        self.cursor.execute('''
            UPDATE DailyCalories SET Goal = ? WHERE Date = ?
        ''', (goal, datetime.datetime.now().strftime('%Y-%m-%d')))
        self.conn.commit()
        self.goal = goal
        
    def track_consumed_calories(self, consumed: float) -> Tuple[bool, float]:
        '''
        Updates the consumed calories for the current day, checks if the goal is achieved,
        and returns a tuple indicating whether the goal is met and the total consumed calories.

        Args:
        - consumed (float): The consumed calories to be added or subtracted.

        Returns:
        - tuple: A tuple containing a boolean indicating goal achievement and the total consumed calories.
        '''
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        self.cursor.execute('''
            UPDATE DailyCalories SET Consumed = Consumed + ? WHERE Date = ?
        ''', (round(consumed, 1), today))
        self.conn.commit()
        
        consumed_calories = self.get_consumed_calories()
        if consumed_calories < self.goal:
            return (True, consumed_calories)
        else:
            return (False, consumed_calories)

    def get_consumed_calories(self) -> float:
        '''
        Retrieves the consumed calories for the current day.

        Returns:
        - float: Consumed calories for the current day.
        '''
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        self.cursor.execute('SELECT Consumed FROM DailyCalories WHERE Date = ?', (today,))
        consumed = self.cursor.fetchone()
        return round(consumed[0],1)
    
    def tracker_history(self) -> List[Tuple[str, float, int]]:
        '''
        Retrieves the daily calories consumption and goal history.

        Returns:
        - list: List of tuples containing date, consumed calories, and goal for each day.
        '''
        self.cursor.execute('SELECT Date, Consumed, Goal FROM DailyCalories ORDER BY Date DESC')
        history = self.cursor.fetchall()
        return history
        
    def calories_counter(self) -> str:
        '''Returns the current daily calories consumption and goal as a counter.'''
        consumed = self.get_consumed_calories()
        goal = self.goal
        return f"\nDaily Calories: {consumed}/{goal} kcal"

    def is_saved(self, exercise_name: str) -> bool:
        '''
        Checks if an exercise is saved.

        Args:
        - exercise_name (str): Name of the exercise.

        Returns:
        - bool: True if the exercise is saved, False otherwise.
        '''
        self.cursor.execute('SELECT COUNT(*) FROM SavedExercises WHERE ExerciseName = ?', (exercise_name,))
        count = self.cursor.fetchone()[0]
        return count > 0
    
    def add_save(self, exercise_name: str, details: Dict[str, Union[str, int]]) -> None:
        '''
        Adds or updates a saved exercise.

        Args:
        - exercise_name (str): Name of the exercise.
        - details (dict): Exercise details.
        '''
        self.cursor.execute('''
            INSERT OR REPLACE INTO SavedExercises (ExerciseName, ExerciseDetails) VALUES (?, ?)
        ''', (exercise_name, json.dumps(details)))
        self.conn.commit()

    def delete_save(self, exercise_name: str) -> None:
        '''
        Deletes a saved exercise.

        Args:
        - exercise_name (str): Name of the exercise.
        '''
        self.cursor.execute('''
            DELETE FROM SavedExercises WHERE ExerciseName = ?
        ''', (exercise_name,))
        self.conn.commit()

    def get_saves(self) -> DataType:
        '''
        Retrieves all saved exercises.

        Returns:
        - list: List of dictionaries containing saved exercises' details.
        '''
        self.cursor.execute('SELECT ExerciseDetails FROM SavedExercises')
        retrieved_data_tuples = self.cursor.fetchall()
        # Convert the list of tuples back to a list of dictionaries.
        retrieved_data = [json.loads(item[0]) for item in retrieved_data_tuples]
        return retrieved_data
    
    def remove_all_saves(self) -> None:
        '''Removes all saved exercises.'''
        confirmation = input("\nAre you sure you want to remove all saved exercises? (y/n): ").lower()
        if confirmation == 'y':
            self.cursor.execute('DELETE FROM SavedExercises')
            self.conn.commit()
            print("All saves have been removed.")
        else:
            print("Operation canceled.")
    
    def add_history(self, food_details: DataType) -> None:
        '''
        Adds searched food to the history.

        Args:
        - food_details (list): List of dictionaries containing food details.
        '''
        # Since food_details is a list of dictionaries, convert them to a list of tuples to insert all data in a batch.
        data_to_store = [(json.dumps(item),) for item in food_details]

        self.cursor.executemany('''
            INSERT INTO SearchedFoodHistory (FoodDetails) VALUES (?)
        ''', data_to_store)

        # Keep only the latest 10 entries in history
        self.cursor.execute('''
            DELETE FROM SearchedFoodHistory 
            WHERE ROWID NOT IN (
                SELECT ROWID FROM SearchedFoodHistory ORDER BY ROWID DESC LIMIT 10
            )
        ''')
        
        self.conn.commit()

    def get_history(self) -> DataType:
        '''
        Retrieves food search history.

        Returns:
        - list: List of dictionaries containing food search history.
        '''
        self.cursor.execute('SELECT * FROM SearchedFoodHistory ORDER BY ROWID DESC')
        retrieved_data_tuples = self.cursor.fetchall()
        # Convert the list of tuples back to a list of dictionaries
        retrieved_data = [json.loads(item[0]) for item in retrieved_data_tuples]
        return retrieved_data
        
    def clear_history(self) -> None:
        '''Clears the food search history.'''
        confirmation = input("\nAre you sure you want to clear the search history? (y/n): ").lower()
        if confirmation == 'y':
            self.cursor.execute('DELETE FROM SearchedFoodHistory')
            self.conn.commit()
            print("History has been cleared.")
        else:
            print("Operation canceled.")

class Pagination:
    def __init__(self, user_data: UserData):
        '''
        Initializes the Pagination object, setting the initial page size and preparing for pagination.

        Args:
        - user_data (UserData): The UserData object to be used for tracking user-specific data.
        '''
        self.user_data = user_data
        self.page_size = self.load_page_size()
    
    def load_page_size(self) -> int:
        '''
        Loads the page size from a configuration file.

        Returns:
        - int: The loaded page size.
        '''
        with open('config.txt', 'r') as config_file:
            data = json.load(config_file)
            return data.get('page_size', 1)
    
    def set_page_size(self) -> None:
        '''
        Sets the page size interactively.

        Updates:
        - Updates the `page_size` attribute.
        - Writes the new page size to the configuration file.
        '''
        while True:
            try:
                new_size = input("\nEnter new page size (max 3): ")
                if new_size.lower() == 'cancel':
                    break
                else:
                    new_size = int(new_size)
                if 1 <= new_size <= 3:
                    self.page_size = new_size
                    with open('config.txt', 'r+') as config_file:
                        data = json.load(config_file)
                        data['page_size'] = self.page_size
                        config_file.seek(0)
                        json.dump(data, config_file)
                    print("\nPage size has been configured.")
                    break
                else:
                    print("\nAllowed page size is 1 to 3.")
            except ValueError:
                print("\nInvalid input! Please enter a number.")
    
    def display_exercise(self) -> None:
        '''Displays exercise details.'''
        print(f"\nLet's dive into this exercise!")
        print(f"Exercise Name: {self.display_data['name']}")
        print(f"Type: {self.display_data['type']}")
        print(f"Muscle: {self.display_data['muscle']}")
        print(f"Equipment: {self.display_data['equipment']}")
        print(f"Difficulty: {self.display_data['difficulty']}")
        print(f"Instructions: {self.display_data['instructions']}")

    def display_nutrition(self) -> None:
        '''Displays nutrition details.'''
        print("\nNutrition Information:")
        print(f"Name: {self.display_data['name']}")
        print(f"Calories: {self.display_data['calories']}")
        print(f"Serving Size: {self.display_data['serving_size_g']}g")
        print(f"Total Fat: {self.display_data['fat_total_g']}g")
        print(f"Saturated Fat: {self.display_data['fat_saturated_g']}g")
        print(f"Protein: {self.display_data['protein_g']}g")
        print(f"Sodium: {self.display_data['sodium_mg']}mg")
        print(f"Potassium: {self.display_data['potassium_mg']}mg")
        print(f"Cholesterol: {self.display_data['cholesterol_mg']}mg")
        print(f"Total Carbohydrates: {self.display_data['carbohydrates_total_g']}g")
        print(f"Fiber: {self.display_data['fiber_g']}g")
        print(f"Sugar: {self.display_data['sugar_g']}g")
    
    def display_page(self) -> None:
        '''Displays current page.'''
        print(f"\nPage {self.current_page}/{self.total_pages}:")
        
        start_index = (self.current_page - 1) * self.page_size
        end_index = start_index + self.page_size
        page_data = self.data[start_index:end_index]
        # Initialize variables to track cumulative nutrition values for the displayed page.
        self.serving_size_check = True
        self.mindful_food = ''  # Foods to be mindful of.
        self.page_calories = 0
        self.page_fat = 0
        self.page_protein = 0
        self.page_sugar = 0
        
        if not page_data:
            self.display_data = False
            print("No results found. Keep pushing!")
        else:
            for data in page_data:
                self.display_data = data
                if self.mode == 'exercise':
                    self.display_exercise()
                elif self.mode == 'nutrition':
                    # Accumulate nutrition values for the displayed page.
                    serving_size = self.display_data.get('serving_size_g', 100)
                    factor = 100 / serving_size  # To calculate nutritions per 100g.
                    calories = self.display_data.get('calories', 0) * factor
                    # Smart condition checking.
                    if serving_size >= 100 and self.serving_size_check:
                        # This block won't get executed after check modifies once.
                        self.serving_size_check = True
                    elif not self.serving_size_check:
                        # Enter block in second food if check was modified.
                        if serving_size < 100 and calories > 300:
                            # Write food name to mindful_food if thresholds met.
                            self.mindful_food += f" and {self.display_data.get('name')}"
                    else:
                        # This block will get executed only once when check modifies.
                        if serving_size < 100 and calories > 300:
                            self.serving_size_check = False
                            self.mindful_food += self.display_data.get('name')
                    
                    self.page_calories += calories
                    self.page_fat += self.display_data.get('fat_total_g', 0) * factor
                    self.page_protein += self.display_data.get('protein_g', 0) * factor
                    self.page_sugar += self.display_data.get('sugar_g', 0) * factor
                    self.display_nutrition()
    
    def nutritional_advice(self) -> str:
        '''
        Provides nutritional advice based on the displayed page.

        Returns:
        - str: Nutritional advice based on the optimised calculations.
        '''
        advice = ''
        if self.page_calories < 100:
            advice += "Low-calorie: Suitable for a healthy diet. Consider incorporating a variety of nutrient-dense foods."
        elif 100 <= self.page_calories <= 300:
            if 10 <= self.page_fat <= 20 and 5 <= self.page_protein <= 20 and self.page_sugar <= 10:
                advice += "Moderate-calorie: Balanced nutritional content. Enjoy in moderation as part of a well-rounded diet."
            else:
                advice = "Moderate-calorie: Consider optimizing your nutritional balance."
                if self.page_fat < 10:
                    advice += " Increase healthy fats for sustained energy."
                elif self.page_fat > 20:
                    advice += " Limit saturated fats for heart health."
                if self.page_protein < 5:
                    advice += " Include more protein sources for muscle maintenance."
                if self.page_sugar > 10:
                    advice += " Be mindful of added sugars for overall well-being."
                if not self.serving_size_check:
                    advice += f"\nBe mindful of {self.mindful_food}. Small amount occasionally can be okay, but try to focus on a balanced diet overall."
        else:
            advice += "High-calorie: Consider consuming in moderation. Check nutritional values for a balanced and varied diet."
            if not self.serving_size_check:
                advice += f"\nBe mindful of {self.mindful_food}. Small amount occasionally can be okay, but try to focus on a balanced diet overall."
    
        return advice
        
    def save_unsave(self) -> str:
        '''
        Returns appropriate option for saving or unsaving exercise.

        Returns:
        - str: Option string for saving or unsaving an exercise.
        '''
        if self.mode == 'nutrition' or (not self.display_data):
            return ''
        else:
            if self.user_data.is_saved(self.display_data['name']):
                return "u : unsave,   "
            else:
                return "s : save,     "
          
    def input_text(self) -> None:
        '''Displays interactive input options.'''
        if self.mode == 'nutrition' and self.display_data and self.current_page not in self.eaten_pages:
            advice = self.nutritional_advice()
            print(f"\nMy advice on this page's nutrition:\n{advice}")
        
        if self.total_pages <= 1:
            print(f"\n{self.save_unsave()}m : main menu")
        elif self.current_page == 1:
            print(f"\nn : next\n{self.save_unsave()}m : main menu")
        elif self.current_page == self.total_pages:
            print(f"\np : previous\n{self.save_unsave()}m : main menu")
        else:
            print(f"\nn : next,     p : previous\n{self.save_unsave()}m : main menu")
        
        if self.mode == 'nutrition' and self.display_data and self.current_page not in self.eaten_pages:
            print('e : eat(add calorie to daily intake)')
    
    def paginate(self, data: DataType, mode: str) -> None:
        '''
        Paginates through data.

        Args:
        - `data` (list): The data to paginate.
        - `mode` (str): The mode of pagination (exercise or nutrition).
        '''
        self.data = data
        self.total_pages = len(self.data) // self.page_size + (len(self.data) % self.page_size > 0) # True evaluates as 1 and False as 0
        self.current_page = 1
        self.mode = mode
        self.display_page()
        self.eaten_pages = [] # List to track pages where calories have been consumed.
        while True:
            self.input_text()
            user_input = input("Enter: ")
        
            if user_input.lower() == 'n':
                if self.current_page < self.total_pages:
                    self.current_page += 1
                    self.display_page()
                else:
                    print("\nNext page doesn't exist.")
            elif user_input.lower() == 'p':
                if self.current_page > 1:
                    self.current_page -= 1
                    self.display_page()
                else:
                    print("\nPrevious page doesn't exist.")
            elif user_input.lower() == 's' and self.mode == 'exercise' and self.display_data:
                if self.user_data.is_saved(self.display_data['name']):
                    print("\nThis exercise is already saved. Great choice!")
                else:
                    self.user_data.add_save(self.display_data['name'], self.display_data)
                    print("\nExercise has been saved. Keep up the good work!")
            elif user_input.lower() == 'u' and self.mode == 'exercise' and self.display_data:
                if not self.user_data.is_saved(self.display_data['name']):
                    print("\nThis exercise is not saved. Keep track of your progress!")
                else:
                    self.user_data.delete_save(self.display_data['name'])
                    print("\nExercise has been unsaved. Adjusting your routine, I see!")
            elif user_input.lower() == 'e' and self.mode == 'nutrition' and self.display_data:
                if self.current_page not in self.eaten_pages:
                    consumed_calories = self.page_calories
                    check = self.user_data.track_consumed_calories(consumed_calories)
                    self.eaten_pages.append(self.current_page)
                    if check[0]:
                        dialogue = 'Keep it up!'
                    else:
                        dialogue = f"You're {check[1]-self.user_data.goal} kcal over your goal!!"
                    print(f"\n{consumed_calories} calories added to daily intake. {dialogue}")
                else:
                    print("\nYou've already added the food(s) in this page to daily intake.")
            elif user_input.lower() == 'm':
                break
            else:
                print("\nInvalid input. Let's stay on track!")

def select_option(header: str, options: Dict[int, str]) -> str:
    '''
    Displays a menu with numbered options and prompts the user to choose an option.

    Args:
    - header (str): The menu/options header to display.
    - options (dict): A dictionary containing numbered options.

    Returns:
    - str: The selected option.
    '''
    while True:
        try:
            print(header)
            for key, value in options.items():
                print(f"{key}. {value}")
            x = int(input("Choose an option: "))
            selected_option = options.get(x)
            if selected_option:
                return selected_option
            else:
                print("\nPlease choose a correct option.")
        except ValueError:
            print("\nInvalid input! Please enter a number.")

def guided_search() -> None:
    '''Guides the user through selecting exercise parameters such as difficulty, type or muscle, then sets the attributes.'''
    difficulty_options = {
        1: 'Beginner',
        2: 'Intermediate',
        3: 'Expert'
    }
    type_options = {
        1: 'Cardio',
        2: 'Powerlifting',
        3: 'Strength',
        4: 'Stretching'
    }
    muscle_options = {
        1: 'Abdominals',
        2: 'Biceps',
        3: 'Calves',
        4: 'Chest',
        5: 'Forearms',
        6: 'Glutes',
        7: 'Hamstrings',
        8: 'Lats',
        9: 'Lower_back',
        10: 'Quadriceps',
        11: 'Triceps'
    }
    header = "\nSELECT DIFFICULTY"
    difficulty = select_option(header, difficulty_options)
    smoki.difficulty = difficulty

    print("\nDo you want to search by 'type' or 'muscle'?")
    
    while True:
         choice = input("Enter 'type' or 'muscle': ").lower()
         if choice == 'type':
             header = "\nSELECT TYPE"
             type = select_option(header, type_options)
             smoki.type = type
             break
         elif choice == 'muscle':
             header = "\nSELECT MUSCLE"
             muscle = select_option(header, muscle_options)
             smoki.muscle = muscle
             break
         else:
             print("\nPlease choose a correct option.")

def get_input(prompt: str, data_type):
    '''
    Get user input with the specified prompt and convert it to the provided data type. Handles error if any.
    
    Args:
    - prompt (str): The prompt message to display to the user.
    - data_type: The desired data type to convert the user input.
    
    Returns:
    The user input converted to the specified data type.
    '''
    while True:
        try:
            return data_type(input(prompt))
        except ValueError:
            print(f"\nInvalid input. Please enter a valid {data_type.__name__}.")
    
def calorie_calc() -> None:
    '''Calculates and provides suggestions for daily calorie needs, and changes goal if the user agrees to update their daily calorie intake.'''
    def calc_bmr(gender, age, weight, height) -> float:
        '''
        Calculate Basal Metabolic Rate (BMR) based on the Harris-Benedict equation.
    
        Args:
        - gender (str): The gender of the individual ('male' or 'female').
        - age (float): The age of the individual in years.
        - weight (float): The weight of the individual in kilograms.
        - height (float): The height of the individual in centimeters.
    
        Returns:
        The calculated BMR.
        '''
        if gender == 'Male':
            bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        elif gender == 'Female':
            bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
        return bmr
            
    gender_options = {
        1: 'Male',
        2: 'Female'
    }
    weight_goals = {
        1: 'Gain',
        2: 'Lose',
        3: 'Maintain'
    }
    activity_factors = {
        'Sedentary (little or no exercise)': 1.2,
        'Lightly active (1-3 days/week)': 1.375,
        'Moderately active (3-5 days/week)': 1.55,
        'Very active (6-7 days/week)': 1.725,
        'Extremely active (hard exercise & physical job or 2x training)': 1.9
    }
    header = "\nSELECT GENDER"
    gender = select_option(header, gender_options)
    age = get_input("\nEnter your age: ", int)
    weight = get_input("\nEnter your weight in kg: ", float)
    height = get_input("\nEnter your height in cm: ", float)
    
    bmr = calc_bmr(gender, age, weight, height)
    while True:
        try:
            print("\nSELECT ACTIVITY LEVEL")
            for i, (activity, factor) in enumerate(activity_factors.items(), 1):
                print(f"{i}. {activity}")
        
            x = int(input("Choose an option: "))
            if 1 <= x <= len(activity_factors):
                activity_factor = list(activity_factors.values())[x - 1]
                break
            else:
                print("\nPlease choose a correct option.")
        except ValueError:
            print("\nInvalid input! Please enter a number.")
    
    daily_calories = round(bmr * activity_factor)
    suggestion = f"Your estimated daily calories need is {daily_calories}."
    header = "\nSELECT WEIGHT GOAL"
    weight_goal = select_option(header, weight_goals)
    if weight_goal == 'Gain':
        daily_calories += 500
        suggestion += f"\nTo gain weight, aim for a daily caloric intake of approximately {daily_calories} kcal."
    elif weight_goal == 'Lose':
        daily_calories -= 500
        suggestion += f"\nTo lose weight, aim for a daily caloric intake of approximately {daily_calories} kcal."
    else:
        suggestion += "\nYour calculated calorie needs are suitable for maintaining your current weight. Consume calories around this amount to stay in balance."
    print(suggestion)
    while True:
        update_goal = input(f"\nWould you like to set {daily_calories} kcal as your daily calories goal? (y/n): ").lower()
        if update_goal == 'y':
            user_data.config_calories_goal(daily_calories)
            print(f"\nGreat! Your daily calories goal has been changed to {daily_calories} kcal.")
            break
        elif update_goal == 'n':
            print("\nNo problem! You can always adjust your daily calories goal later.")
            break
        else:
            print("\nInvalid input. Please enter 'y' or 'n'.")

def calories_tracker_menu() -> None:
    '''Displays options related to the calories tracker and handles user input accordingly.'''
    while True:
        options = {
            1: 'Calorie Intake Calculator',
            2: 'View Tracker History',
            3: 'Change Calories Intake Goal',
            4: 'Add Daily Calories',
            5: 'Subtract Daily Calories',
            6: 'Back to Main Menu'
        }
        header = f"{user_data.calories_counter()}\n\033[3mSmokiFit─ CALORIES TRACKER \033[0m"
        choice = select_option(header, options)
        if choice == 'Calorie Intake Calculator':
            calorie_calc()
        elif choice == 'View Tracker History':
            history = user_data.tracker_history()
            print("\nLast 7 days history:")
            # The < character is a formatting option that aligns the content to the left within the specified width.
            print(f"{'Date': <13}{'Consumed (kcal)': <17}Goal (kcal)")
            for entry in history:
                print(f"{entry[0]: <13}{entry[1]: <17}{entry[2]}")
        elif choice == 'Change Calories Intake Goal':
            new_goal = get_input("\nEnter your new daily calories intake goal: ", int)
            user_data.config_calories_goal(new_goal)
            print(f"\nGreat! Your daily calories goal has been changed to {new_goal} kcal.")
        elif choice == 'Add Daily Calories':
            while True:
                try:
                    value = int(input("\nEnter how many calories to add: "))
                    user_data.track_consumed_calories(value)
                    print(f"\nGot it, {value} calories added to daily intake.")
                    break
                except ValueError:
                    print("\nSilly you, calories should be in number.")
        elif choice == 'Subtract Daily Calories':
            while True:
                try:
                    value = int(input("\nEnter how many calories to subtract: "))
                    user_data.track_consumed_calories(0-value)
                    print(f"\nGot it, {value} calories subtracted from daily intake.")
                    break
                except ValueError:
                    print("\nSilly you, calories should be in number.")
        elif choice == 'Back to Main Menu':
            break
    
def settings_menu() -> None:
    '''Displays the settings menu and handle user interactions.'''
    while True:
        settings_options = {
            1: 'Change API Key',
            2: 'Configure Page Size',
            3: 'Remove All Saves',
            4: 'Clear History',
            5: 'Back to Main Menu'
        }
        header = "\n\033[3mSmokiFit── SETTINGS \033[0m"
        choice = select_option(header, settings_options)

        if choice == 'Change API Key':
            print("\nFree API key at \033[4mhttps://api-ninjas.com\033[0m.")
            smoki.key = smoki.ask_for_key()
        elif choice == 'Configure Page Size':
            paginator.set_page_size()
        elif choice == 'Remove All Saves':
            user_data.remove_all_saves()
        elif choice == 'Clear History':
            user_data.clear_history()
        elif choice == 'Back to Main Menu':
            break

def main_menu() -> None:
    '''Displays the main menu with various options and handles user input accordingly.'''
    def main() -> None:
        '''The main function orchestrating the user interaction with the fitness guide.'''
        data = json.loads(smoki.get_data())
        mode = smoki.mode
        if mode == 'nutrition':
            if data:
                user_data.add_history(data)

        paginator.paginate(data, mode)
        
    while True:
        main_options = {
            1: 'Search Exercise - Guided',
            2: 'Search Exercise - Named',
            3: 'Search Nutrition of Food',
            4: 'Calories Tracker',
            5: 'View Saved Exercises',
            6: 'View Nutrition History',
            7: 'Settings',
            8: 'Exit'
        }
        # \033[3m highlights text and \033[0m resets it.
        header = f"{user_data.calories_counter()}\n\033[3mSmokiFit── MAIN MENU \033[0m"
        choice = select_option(header, main_options)

        if choice == 'Search Exercise - Guided':
            smoki.mode = 'exercise'
            guided_search()
            main()
        elif choice == 'Search Exercise - Named':
            smoki.mode = 'exercise'
            name = input("\nEnter name of exercise to search: ")
            smoki.name = name
            main()
        elif choice == 'Search Nutrition of Food':
            smoki.mode = 'nutrition'
            print("\nTip: You can enter serving sizes and search multiple foods using ‘and’ between names.")
            food = input("\nEnter name of food: ")
            smoki.food = food
            main()
        elif choice == 'Calories Tracker':
            calories_tracker_menu()
        elif choice == 'View Saved Exercises':
            saved = user_data.get_saves()
            paginator.paginate(saved, 'exercise')
        elif choice == 'View Nutrition History':
            history = user_data.get_history()
            paginator.paginate(history, 'nutrition')
        elif choice == 'Settings':
            settings_menu()
        elif choice == 'Exit':
            print('\nBye bro. See you again.')
            break
        
# Try to instantiate a Trainer object.
try:
    smoki = Trainer()
# Handle a ConnectionError, which might occur if there is no internet connection.
except requests.exceptions.ConnectionError:
    print("Please make sure you have an active internet connection.")
# If no exception occurred, proceed with the following actions.
else:
    user_data = UserData()
    paginator = Pagination(user_data)
    main_menu()
    user_data.cursor.close()
    user_data.conn.close()
  
