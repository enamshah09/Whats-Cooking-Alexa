from flask import Flask
from flask_ask import Ask, statement, question, session
import datetime
import requests
import logging
import os

app = Flask(__name__)
# app.config['ASK_APPLICATION_ID'] = 'amzn1.ask.skill.2b01e5b0-9f38-41eb-bb0c-d57ab17b5d5a'

index = 0
lenJson = 0
response = []
recipe = ''
id = '-1'
instructionSteps = []
lastInstruction = 0
g_ingredients = []
ask = Ask(app, '/')

if os.getenv('GREETINGS_DEBUG_EN', False):
    logging.getLogger('flask_ask').setLevel(logging.DEBUG)

@ask.launch
def launch():
    speech_text = "Welcome to our smart recipe finder app. Tasty Dish Guaranteed. " \
                  "Ask the Master Chef what can I cook today?. Just tell Master Chef what Ingredients do you have";
    reprompt_text = "You can say Give me recipe for Tomato onion and chilly etc. ";
    return question(speech_text).reprompt(reprompt_text)

@ask.intent('NewIngredientIntent')
def handle_new_ingredient_intent(ingredients):
    global index
    index = 0
    global lastInstruction
    lastInstruction = 0
    global instructionSteps
    instructionSteps = []
    global response
    response = getRecipe(ingredients)
    if len(response) <= 0 :
        speech_text = 'Sorry! No recipe found with ingredients ' + str(ingredients) + ' Try ' \
                        'Adding or removing an ingredient'
        reprompt_text = 'You can add ingredient by saying add Chicken or To Remove say remove Tomato '
        return question(speech_text).reprompt(reprompt_text)
    speech_text = 'Top recipe I found is. '
    speech_text += response[index]['title']
    global id
    id = response[index]['id']
    global lenJson
    lenJson = len(response)
    speech_text += ' Would you like Master Chef to walk you through this recipe step by step?'
    reprompt_text = ' You can say start cooking or yes for detailed instructions or No for new dish'
    session.attributes['new_ingredient_intent'] = True
    return question(speech_text).reprompt(reprompt_text)

@ask.intent('NextRecipe')
def handle_next_recipe():
    if 'new_ingredient_intent' in session.attributes:
        speech_text = 'your next recipe is. '
        global index
        index += 1
        reprompt_text = '';
        if index < lenJson:
            global id
            id = response[index]['id']
            speech_text += response[index]['title']
            speech_text += '. Would you like Master Chef to walk you through this recipe step by step?'
            reprompt_text = ' You can say start cooking or yes for detailed instructions or No for new dish'
        else:
            speech_text = 'No more Recipe. Try adding or removing ingredients to master chef '
    else:
        speech_text = 'Wrong Invocation'
        return statement(speech_text)
    return question(speech_text).reprompt(reprompt_text)

@ask.intent('InstructionSetIntent')
def handle_instruction_set_intent():
    if 'new_ingredient_intent' in session.attributes:
        global instructionSteps
        instructionSteps = getInstructions(id)

        if len(instructionSteps[0]['steps']) > 0:
            speech_text = 'Here are the Instructions. Step. '
            speech_text += str(instructionSteps[0]['steps'][lastInstruction]['number']) + ' ' + \
                           str(instructionSteps[0]['steps'][lastInstruction]['step']) +\
                           ". When ready say Next Step"
        else:
            speech_text = 'There are no Instructions for this Dish. Enjoy your meal'
            return statement(speech_text)
    else:
        speech_text = 'For instruction on how to make a dish you must select a recipe first'
        return question(speech_text)

    return question(speech_text)


@ask.intent('NextInstructionIntent')
def handle_next_instruction_intent():
    global lastInstruction
    lastInstruction += 1
    print (str(len(instructionSteps[0]['steps'])) + ' '+ str(lastInstruction))
    speech_text = '';
    if lastInstruction == (len(instructionSteps[0]['steps']) - 1):
        speech_text += ' you are almost done. Final Step ' + ' ' + \
                      str (instructionSteps[0]['steps'][lastInstruction]['step']) + ". Enjoy your meal. Good Bye"
        return statement(speech_text)
    elif lastInstruction < (len(instructionSteps[0]['steps']) - 1):
        speech_text += 'step ' + str(instructionSteps[0]['steps'][lastInstruction]['number']) + \
                      str(instructionSteps[0]['steps'][lastInstruction]['step']) + ". When ready say Next Step"
    else:
        speech_text = "Your dish is completed. Enjoy the Dish";
        return statement(speech_text)
    return question(speech_text)


@ask.intent('AddIngredientIntent')
def handle_add_ingredient(ingredients):
    global g_ingredients
    if ingredients in g_ingredients:
        speech_text = 'This ingredient is already present try adding some other ingredient'
        return question(speech_text)
    else:
        temp = ' '.join(g_ingredients)
        g_ingredients = ingredients + ' ' + temp
        print (g_ingredients)
        return handle_new_ingredient_intent(g_ingredients)


@ask.intent('RemoveIngredientIntent')
def handle_add_ingredient(ingredients):
    global g_ingredients
    print (ingredients)
    print (g_ingredients)
    if ingredients in g_ingredients:
        g_ingredients.remove(ingredients)
    else:
        speech_text = 'Sorry this ingredient is not present. please try another ingredient'
        return question(speech_text)
    temp = ' '.join(g_ingredients)
    g_ingredients = temp
    print (g_ingredients)
    return handle_new_ingredient_intent(g_ingredients)

@ask.intent('AMAZON.StopIntent')
def handle_stop_intent():
    speech_text = 'Good Bye! Have a Nice Day'
    return statement(speech_text)

def getInstructions(id):
    url = 'https://spoonacular-recipe-food-nutrition-v1.p.mashape.com/recipes/' \
          + str(id) + '/analyzedInstructions?stepBreakdown=true'
    headers = {'X-Mashape-Key':'your Key','Accept':'application/json'}
    print (url)
    r = requests.get(url,headers=headers)
    instruction = r.json()
    print (instruction)
    return instruction


def getRecipe(ingredients):
    #li = ['tomato','onion']
    global g_ingredients
    g_ingredients = ingredients.split()
    all_ingredients = ",".join(g_ingredients)
    print (all_ingredients)
    url = 'https://spoonacular-recipe-food-nutrition-v1.p.mashape.com/recipes/' \
          'findByIngredients?fillIngredients=false&ingredients='+ all_ingredients + '&limitLicense=false&number=5&ranking=1'
    headers = {'X-Mashape-Key':'your Key' ,'Accept':'application/json'}
    print (url)
    r = requests.get(url,headers=headers)
    # r.content = r._content.replace('\\', '')
    recipe = r.json()
    print (recipe)
    return recipe


if __name__ == '__main__':
    app.config['ASK_VERIFY_REQUESTS'] = False
    port = int(os.getenv('PORT',5000))
    print ("Starting app on port %d" % port)
    app.run(debug=False,port=port,host='0.0.0.0')
