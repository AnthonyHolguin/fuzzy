import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


# Universe of discourse and defuzzify_method
Puntuacion_Numerica= ctrl.Antecedent(np.arange(1,5.25,0.25),'Puntuacion Numerica')
Puntuacion_Sentimiento = ctrl.Antecedent(np.arange(-1,1.2,0.2),'Puntuacion Sentimiento')
Puntuacion_Confianza = ctrl.Consequent(np.arange(0.1,1.1,0.1),'Puntuacion Confianza', defuzzify_method='LOM') #LOM

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

# Puntuación Confianza
Puntuacion_Confianza['Bajo'] = fuzz.trapmf(Puntuacion_Confianza.universe,    [0,0,0.2,0.4])
Puntuacion_Confianza['Medio Bajo'] = fuzz.trimf(Puntuacion_Confianza.universe,[0.2,0.4,0.6])
Puntuacion_Confianza['Medio'] = fuzz.trimf(Puntuacion_Confianza.universe,[0.4,0.6,0.8])
Puntuacion_Confianza['Medio Alto'] = fuzz.trimf(Puntuacion_Confianza.universe,[0.6,0.8,1])
Puntuacion_Confianza['Alto'] = fuzz.trapmf(Puntuacion_Confianza.universe, [0.8,0.9,1,1])

# Rules
# Detecta precisión y genera la puntuación de la evaluación
R1 = ctrl.Rule(Puntuacion_Numerica['Nada adecuado'] & Puntuacion_Sentimiento['Negativo'] , Puntuacion_Confianza['Bajo'])#1 - 0.1 - 0.2
R2 = ctrl.Rule(Puntuacion_Numerica['Poco adecuado'] & Puntuacion_Sentimiento['Negativo'] , Puntuacion_Confianza['Medio Bajo'])#2 - 0.2 - 0.4
R3 = ctrl.Rule(Puntuacion_Numerica['Adecuado'] & Puntuacion_Sentimiento['Neutro']  , Puntuacion_Confianza['Medio'])#3 - 0.3 - 0.6
R4= ctrl.Rule(Puntuacion_Numerica['Bastante adecuado'] & Puntuacion_Sentimiento['Positivo']  , Puntuacion_Confianza['Medio Alto'])#4 - 0.4 - 0.8
R5 = ctrl.Rule(Puntuacion_Numerica['Totalmente adecuado'] & Puntuacion_Sentimiento['Positivo']  , Puntuacion_Confianza['Alto'])#5 - 0.5 - 1
# Detecta imprecisión y genera la puntuación de la evaluaciónMedio
R6 = ctrl.Rule(Puntuacion_Numerica['Nada adecuado'] & Puntuacion_Sentimiento['Positivo']  , Puntuacion_Confianza['Medio Bajo'])
R7 = ctrl.Rule(Puntuacion_Numerica['Nada adecuado'] & Puntuacion_Sentimiento['Neutro']  , Puntuacion_Confianza['Medio Bajo'])
R8 = ctrl.Rule(Puntuacion_Numerica['Poco adecuado'] & Puntuacion_Sentimiento['Positivo']  , Puntuacion_Confianza['Medio Bajo'])
R9 = ctrl.Rule(Puntuacion_Numerica['Poco adecuado'] & Puntuacion_Sentimiento['Neutro']  , Puntuacion_Confianza['Medio Bajo'])
R10 = ctrl.Rule(Puntuacion_Numerica['Adecuado'] & Puntuacion_Sentimiento['Positivo']  , Puntuacion_Confianza['Medio'])
R11 = ctrl.Rule(Puntuacion_Numerica['Adecuado'] & Puntuacion_Sentimiento['Negativo']  , Puntuacion_Confianza['Medio Bajo'])
R12 = ctrl.Rule(Puntuacion_Numerica['Bastante adecuado'] & Puntuacion_Sentimiento['Neutro'] , Puntuacion_Confianza['Medio'])
R13 = ctrl.Rule(Puntuacion_Numerica['Bastante adecuado'] & Puntuacion_Sentimiento['Negativo'] , Puntuacion_Confianza['Medio Bajo'])
R14 = ctrl.Rule(Puntuacion_Numerica['Totalmente adecuado'] & Puntuacion_Sentimiento['Neutro'] , Puntuacion_Confianza['Medio'])
R15= ctrl.Rule(Puntuacion_Numerica['Totalmente adecuado'] & Puntuacion_Sentimiento['Negativo'] , Puntuacion_Confianza['Medio Bajo'])

# Control System
tipping_ctrl = ctrl.ControlSystem([R1,R2,R3,R4,R5,R6,R7,R8,R9,R10,R11,R12,R13,R14,R15])
tipping = ctrl.ControlSystemSimulation(tipping_ctrl)

def apply_fuzzy(df):
    tipping.input['Puntuacion Numerica'] = df['PuntuacionNumerica']
    tipping.input['Puntuacion Sentimiento'] = df['PuntuacionSentimiento']
    #output FUZZY
    tipping.compute()
    return round(tipping.output['Puntuacion Confianza'],8)

def apply_model(data):
    
    data['PuntuacionConfianza'] = data.apply(apply_fuzzy, axis=1)
    return data
