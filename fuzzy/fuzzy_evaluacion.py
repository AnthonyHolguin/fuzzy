import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


# Universe of discourse and defuzzify_method
Puntuacion_Numerica = ctrl.Antecedent(np.arange(1,5.25,0.25),'Puntuacion Numerica')
Puntuacion_Sentimiento = ctrl.Antecedent(np.arange(-1,1.2,0.2),'Puntuacion Sentimiento')
Puntuacion_Evaluacion = ctrl.Consequent(np.arange(1,5.25,0.25),'Puntuacion Evaluacion', defuzzify_method='LOM')

# Fuzzification
# Puntuación Númerica
Puntuacion_Numerica['Nada adecuado'] = fuzz.trapmf(Puntuacion_Numerica.universe, [1, 1,1.25, 2])
Puntuacion_Numerica['Poco adecuado'] = fuzz.trimf(Puntuacion_Numerica.universe, [1,2,3])
Puntuacion_Numerica['Adecuado'] = fuzz.trimf(Puntuacion_Numerica.universe, [2,3,4])
Puntuacion_Numerica['Bastante adecuado'] = fuzz.trimf(Puntuacion_Numerica.universe, [3,4,5])
Puntuacion_Numerica['Totalmente adecuado'] = fuzz.trapmf(Puntuacion_Numerica.universe, [4,4.75,5,5])

# Puntuación Sentimiento
Puntuacion_Sentimiento['Positivo'] = fuzz.trapmf(Puntuacion_Sentimiento.universe,[0,0.8,1,1])
Puntuacion_Sentimiento['Neutro'] = fuzz.trimf(Puntuacion_Sentimiento.universe,[-1,0,1])
Puntuacion_Sentimiento['Negativo'] = fuzz.trapmf(Puntuacion_Sentimiento.universe, [-1,-1,-0.8,0])

# Puntuación Evaluación
Puntuacion_Evaluacion['Nada adecuado'] = fuzz.trapmf(Puntuacion_Evaluacion.universe,   [1, 1,1.25, 2])
Puntuacion_Evaluacion['Poco adecuado'] = fuzz.trimf(Puntuacion_Evaluacion.universe,[1,2,3])
Puntuacion_Evaluacion['Adecuado'] = fuzz.trimf(Puntuacion_Evaluacion.universe,[2,3,4])
Puntuacion_Evaluacion['Bastante adecuado'] = fuzz.trimf(Puntuacion_Evaluacion.universe,[3,4,5])
Puntuacion_Evaluacion['Totalmente adecuado'] = fuzz.trapmf(Puntuacion_Evaluacion.universe, [4,4.75,5,5])

# Rules
# Detecta precisión y genera la puntuación de la evaluación
R1 = ctrl.Rule(Puntuacion_Numerica['Nada adecuado'] & Puntuacion_Sentimiento['Negativo'] , Puntuacion_Evaluacion['Nada adecuado'])
R2 = ctrl.Rule(Puntuacion_Numerica['Poco adecuado'] & Puntuacion_Sentimiento['Negativo'] , Puntuacion_Evaluacion['Poco adecuado'])
R3 = ctrl.Rule(Puntuacion_Numerica['Adecuado'] & Puntuacion_Sentimiento['Neutro']  , Puntuacion_Evaluacion['Adecuado'])
R4= ctrl.Rule(Puntuacion_Numerica['Bastante adecuado'] & Puntuacion_Sentimiento['Positivo']  , Puntuacion_Evaluacion['Bastante adecuado'])
R5 = ctrl.Rule(Puntuacion_Numerica['Totalmente adecuado'] & Puntuacion_Sentimiento['Positivo']  , Puntuacion_Evaluacion['Totalmente adecuado'])
# Detecta imprecisión y genera la puntuación de la evaluación
R6 = ctrl.Rule(Puntuacion_Numerica['Nada adecuado'] & Puntuacion_Sentimiento['Positivo']  , Puntuacion_Evaluacion['Poco adecuado'])
R7 = ctrl.Rule(Puntuacion_Numerica['Nada adecuado'] & Puntuacion_Sentimiento['Neutro']  , Puntuacion_Evaluacion['Poco adecuado'])
R8 = ctrl.Rule(Puntuacion_Numerica['Poco adecuado'] & Puntuacion_Sentimiento['Positivo']  , Puntuacion_Evaluacion['Poco adecuado'])
R9 = ctrl.Rule(Puntuacion_Numerica['Poco adecuado'] & Puntuacion_Sentimiento['Neutro']  , Puntuacion_Evaluacion['Poco adecuado'])
R10 = ctrl.Rule(Puntuacion_Numerica['Adecuado'] & Puntuacion_Sentimiento['Positivo']  , Puntuacion_Evaluacion['Adecuado'])
R11 = ctrl.Rule(Puntuacion_Numerica['Adecuado'] & Puntuacion_Sentimiento['Negativo']  , Puntuacion_Evaluacion['Poco adecuado'])
R12 = ctrl.Rule(Puntuacion_Numerica['Bastante adecuado'] & Puntuacion_Sentimiento['Neutro'] , Puntuacion_Evaluacion['Adecuado'])
R13 = ctrl.Rule(Puntuacion_Numerica['Bastante adecuado'] & Puntuacion_Sentimiento['Negativo'] , Puntuacion_Evaluacion['Poco adecuado'])
R14 = ctrl.Rule(Puntuacion_Numerica['Totalmente adecuado'] & Puntuacion_Sentimiento['Neutro'] , Puntuacion_Evaluacion['Adecuado'])
R15= ctrl.Rule(Puntuacion_Numerica['Totalmente adecuado'] & Puntuacion_Sentimiento['Negativo'] , Puntuacion_Evaluacion['Poco adecuado'])


# Control System
tipping_ctrl = ctrl.ControlSystem([R1,R2,R3,R4,R5,R6,R7,R8,R9,R10,R11,R12,R13,R14,R15])
tipping = ctrl.ControlSystemSimulation(tipping_ctrl)


def apply_fuzzy(df):
    tipping.input['Puntuacion Numerica'] = df['PuntuacionNumerica']
    tipping.input['Puntuacion Sentimiento'] = df['PuntuacionSentimiento']

    #output FUZZY
    tipping.compute()
    return round(tipping.output['Puntuacion Evaluacion'],2)


def apply_model(data):
    
    data['PuntuacionEvaluacion'] = data.apply(apply_fuzzy, axis=1)
    return data
