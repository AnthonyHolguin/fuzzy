from operator import and_
from pprint import pprint
from uuid import uuid4
from flask.app import Flask
from flask_restx import fields, marshal, reqparse
from flask_restx.api import Api
from flask_restx.resource import Resource
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import aliased
from sqlalchemy.sql import and_

from fuzzy import fuzzy_confianza, fuzzy_evaluacion
import pandas as pd


# flask instance
app: Flask = Flask(__name__)

# flask config
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'postgresql+psycopg2://urhteshnxudiza:667952d77f32f2c171fdee167dcae967a3cc7c80de3cf9e5b70a6eafb897df14@ec2-34-196-238-94.compute-1.amazonaws.com:5432/d6a74uguvg6ed4')

# flask extensions
api: Api = Api(
    app,
    title='API fuzzy',
    catch_all_404s=True
)
db: SQLAlchemy = SQLAlchemy(app)
db.reflect()


# error handlers
@api.errorhandler(Exception)
def handle_custom_exception(error):
    return {'message': str(error)}, 500


# models
class Evaluacion(db.Model):
    __tablename__ = 'evaluacion'


class FtEstudiante(db.Model):
    __tablename__ = 'ft_estudiante'


class Grupo(db.Model):
    __tablename__ = 'grupo'


class AsignacionEvaluacion(db.Model):
    __tablename__ = 'asignacion_evaluacion'


class TipoAgrupamiento(db.Model):
    __tablename__ = 'tipo_agrupamiento'


class EnviarTarea(db.Model):
    __tablename__ = 'enviar_tarea'


class Actividad(db.Model):
    __tablename__ = 'actividad'


class Criterio(db.Model):
    __tablename__ = 'criterio'


class DatosUnificados(db.Model):
    __tablename__ = 'datos_unificados'


# schemas
dataSchema = api.model('dataSchema', {
    'idactividad': fields.Integer,
    'idgrupo_evaluador': fields.Integer,
    'grupo_evaluador': fields.String,
    'rol': fields.String,
    'idestudiante': fields.String,
    'estudiante': fields.String(
        attribute=lambda obj: f'{obj.apellido1} {obj.apellido2} {obj.nombres}'.upper()),
    'idgrupo_evaluado': fields.Integer,
    'grupo_evaluado': fields.String,
    'puntuacion_evaluacion_promedio': fields.Float,
    'puntuacion_evaluacion_mediana': fields.Float,
    'grupo_puntuacion_evaluacion_promedio': fields.Float,
    'grupo_puntuacion_evaluacion_mediana': fields.Float,
    'grupo_puntuacion_confianza_promedio': fields.Float,
    'grupo_puntuacion_confianza_mediana': fields.Float
})

paginationSchema = api.model('paginationSchema', {
    'items': fields.List(fields.Nested(dataSchema)),
    'page': fields.Integer,
    'per_page': fields.Integer,
    'pages': fields.Integer,
    'next_num': fields.Integer,
    'prev_num': fields.Integer
})

messageSchema = api.model('messageSchema', {
    'message': fields.String
})

activitySchema = api.model('activitySchema', {
    'idactividad': fields.Integer(default=1)
})

paginationParser = reqparse.RequestParser()
paginationParser.add_argument('idactividad', type=int, default=1, location='args',
                              help='ID actividad')
paginationParser.add_argument('page', type=int, default=1, location='args',
                              help='Page')
paginationParser.add_argument('per_page', type=int, default=100, location='args',
                              help='Items per page')


def applyModelsFuzzy(idactividad: int):
    with db.session.begin():
        columns = ['idevaluacion', 'PuntuacionNumerica',
                   'PuntuacionSentimiento']

        rowsConfianza = db.session.query(
            Evaluacion.idevaluacion,
            Evaluacion.puntuacion,
            Evaluacion.polaridad
        )\
            .join(EnviarTarea)\
            .filter(
                Evaluacion.puntuacion.is_not(None),
                Evaluacion.polaridad.is_not(None),
                Evaluacion.idevaluacion_evaluador.is_not(None),
                EnviarTarea.idactividad == idactividad
        ).all()

        rowsEvaluacion = db.session.query(
            Evaluacion.idevaluacion,
            Evaluacion.puntuacion,
            Evaluacion.polaridad
        )\
            .join(EnviarTarea)\
            .filter(
                Evaluacion.puntuacion.is_not(None),
                Evaluacion.polaridad.is_not(None),
                Evaluacion.idevaluacion_evaluador.is_(None),
                EnviarTarea.idactividad == idactividad
        ).all()

        if rowsEvaluacion:
            DataCriterio_tarea = pd.DataFrame(rowsEvaluacion, columns=columns)
            DataCriterio_tarea2 = fuzzy_evaluacion.apply_model(
                DataCriterio_tarea)

            for item in DataCriterio_tarea2.to_dict('records'):
                db.session.query(Evaluacion)\
                    .filter_by(idevaluacion=item['idevaluacion'])\
                    .update(
                        {'puntuacion_evaluacion': item['PuntuacionEvaluacion']},
                        synchronize_session=False
                )

        if rowsConfianza:
            DataCriterio_calidad = pd.DataFrame(rowsConfianza, columns=columns)
            DataCriterio_calidad2 = fuzzy_confianza.apply_model(
                DataCriterio_calidad)

            for item in DataCriterio_calidad2.to_dict('records'):
                db.session.query(Evaluacion)\
                    .filter_by(idevaluacion=item['idevaluacion'])\
                    .update(
                        {'puntuacion_confianza': item['PuntuacionConfianza']},
                        synchronize_session=False
                )

        TipoAgrupamientoEvaluador = aliased(TipoAgrupamiento)
        TipoAgrupamientoEvaluado = aliased(TipoAgrupamiento)

        rowsTarea = db.session.query(
            EnviarTarea.idactividad,
            TipoAgrupamientoEvaluador.idgrupo.label('grupo_evaluador'),
            TipoAgrupamientoEvaluado.idgrupo.label('grupo_evaluado'),
            Evaluacion.idestudiante,
            Evaluacion.puntuacion_evaluacion
        )\
            .select_from(Evaluacion)\
            .join(EnviarTarea)\
            .join(FtEstudiante)\
            .join(AsignacionEvaluacion)\
            .outerjoin(TipoAgrupamientoEvaluador,
                       TipoAgrupamientoEvaluador.idtipo_agrupamiento ==
                       AsignacionEvaluacion.idtipo_agrupamiento_evaluador)\
            .join(TipoAgrupamientoEvaluado,
                  TipoAgrupamientoEvaluado.idtipo_agrupamiento ==
                  AsignacionEvaluacion.idtipo_agrupamiento_evaluado)\
            .filter(
                Evaluacion.idevaluacion_evaluador.is_(None),
                Evaluacion.puntuacion_evaluacion.is_not(None),
                EnviarTarea.idactividad == idactividad
        ).all()

        # calculos de media y mediana
        columns = ['idactividad', 'grupo_evaluador', 'CodigoEvaluado',
                   'Estudiante', 'PuntuacionEvaluacion']
        DataCriterio_tarea = pd.DataFrame(rowsTarea, columns=columns)
        tarea_group = DataCriterio_tarea.groupby([
            'idactividad', 'grupo_evaluador', 'CodigoEvaluado', 'Estudiante'])\
            .agg(['mean', 'median'])
        tarea_group.reset_index(inplace=True)
        tarea_group.columns = list(map(''.join, tarea_group.columns.values))
        tarea_group.columns = [
            'idactividad', 'grupo_evaluador_id', 'grupo_evaluado_id',
            'estudianteid', 'puntuacion_evaluacion_promedio',
            'puntuacion_evaluacion_mediana']

        # limpiar cálculos guardados para guardar nuevamente los cálculos
        DatosUnificados.query.filter_by(idactividad=idactividad).delete()
        datosUnificados = [DatosUnificados(**row)
                           for row in tarea_group.to_dict('records')]
        db.session.bulk_save_objects(datosUnificados)

        rowsDatosUnificados = db.session.query(
            FtEstudiante.rol,
            DatosUnificados.idactividad,
            DatosUnificados.grupo_evaluado_id,
            DatosUnificados.puntuacion_evaluacion_promedio,
            DatosUnificados.puntuacion_evaluacion_mediana
        )\
            .join(FtEstudiante)\
            .filter(DatosUnificados.idactividad == idactividad).all()

        columns = ['rol', 'idactividad', 'grupo_evaluado_id',
                   'puntuacion_evaluacion_promedio',
                   'puntuacion_evaluacion_mediana']
        DataCriterio_tarea = pd.DataFrame(rowsDatosUnificados, columns=columns)
        tarea_group = DataCriterio_tarea.groupby([
            'rol', 'idactividad', 'grupo_evaluado_id'])\
            .agg({
                'puntuacion_evaluacion_promedio': 'mean',
                'puntuacion_evaluacion_mediana': 'median'})
        tarea_group.reset_index(inplace=True)
        tarea_group.columns = [
            'rol', 'idactividad', 'grupo_evaluado_id',
            'grupo_puntuacion_evaluacion_promedio',
            'grupo_puntuacion_evaluacion_mediana']

        for row in tarea_group.to_dict('records'):
            if row['rol'] == 'ESTUDIANTE':
                DatosUnificados.query\
                    .filter(
                        DatosUnificados.iddatounificado.in_(
                            db.session.query(DatosUnificados.iddatounificado)
                            .join(FtEstudiante)
                            .filter(
                                DatosUnificados.idactividad == idactividad,
                                DatosUnificados.grupo_evaluador_id == row['grupo_evaluado_id'],
                                FtEstudiante.rol == row['rol']
                            )
                        )
                    ).update({
                        'grupo_puntuacion_evaluacion_promedio': row['grupo_puntuacion_evaluacion_promedio'],
                        'grupo_puntuacion_evaluacion_mediana': row['grupo_puntuacion_evaluacion_mediana']
                    }, synchronize_session=False)
            else:
                DatosUnificados.query\
                    .filter(
                        DatosUnificados.iddatounificado.in_(
                            db.session.query(DatosUnificados.iddatounificado)
                            .join(FtEstudiante)
                            .filter(
                                DatosUnificados.idactividad == idactividad,
                                DatosUnificados.grupo_evaluado_id == row['grupo_evaluado_id'],
                                FtEstudiante.rol == row['rol']
                            )
                        )
                    ).update({
                        'grupo_puntuacion_evaluacion_promedio': row['grupo_puntuacion_evaluacion_promedio'],
                        'grupo_puntuacion_evaluacion_mediana': row['grupo_puntuacion_evaluacion_mediana']
                    }, synchronize_session=False)

        datosConfianza = db.session.query(
            DatosUnificados.idactividad,
            DatosUnificados.estudianteid,
            DatosUnificados.grupo_evaluado_id,
            Evaluacion.puntuacion_confianza
        )\
            .select_from(DatosUnificados)\
            .join(FtEstudiante)\
            .join(Evaluacion)\
            .join(AsignacionEvaluacion)\
            .join(TipoAgrupamiento,
                  and_(
                      TipoAgrupamiento.idtipo_agrupamiento == AsignacionEvaluacion.idtipo_agrupamiento_evaluador,
                      TipoAgrupamiento.idgrupo == DatosUnificados.grupo_evaluado_id
                  )
                  )\
            .join(
                EnviarTarea,
                and_(
                    EnviarTarea.idenviar_tarea == Evaluacion.idenviar_tarea,
                    EnviarTarea.idactividad == DatosUnificados.idactividad
                ))\
            .filter(
                DatosUnificados.idactividad == idactividad,
                Evaluacion.puntuacion_confianza.is_not(None)
        ).all()

        columns = ['idactividad', 'estudianteid', 'grupo_evaluado_id',
                   'puntuacion_confianza']
        dataConfianza = pd.DataFrame(datosConfianza, columns=columns)
        dataConfianza_group = dataConfianza.groupby([
            'idactividad', 'estudianteid', 'grupo_evaluado_id'])\
            .agg(['mean', 'median'])
        dataConfianza_group.reset_index(inplace=True)
        dataConfianza_group.columns = list(
            map(''.join, dataConfianza_group.columns.values))

        dataConfianza_group.columns = [
            'idactividad', 'estudianteid', 'grupo_evaluado_id',
            'puntuacion_confianza_mean', 'puntuacion_confianza_median']

        for row in dataConfianza_group.to_dict('records'):
            DatosUnificados.query\
                .filter(
                    DatosUnificados.idactividad == row['idactividad'],
                    DatosUnificados.estudianteid == row['estudianteid'],
                    DatosUnificados.grupo_evaluado_id == row['grupo_evaluado_id']
                ).update({
                    'grupo_puntuacion_confianza_promedio': row['puntuacion_confianza_mean'],
                    'grupo_puntuacion_confianza_mediana': row['puntuacion_confianza_median']
                }, synchronize_session=False)


def getData(idactividad):
    GrupoEvaluador = aliased(Grupo)
    GrupoEvaluado = aliased(Grupo)

    return db.session.query(
        DatosUnificados.idactividad,
        GrupoEvaluador.idgrupo.label('idgrupo_evaluador'),
        GrupoEvaluador.nombre.label('grupo_evaluador'),
        FtEstudiante.rol, FtEstudiante.idestudiante,
        FtEstudiante.apellido1, FtEstudiante.apellido2, FtEstudiante.nombres,
        GrupoEvaluado.idgrupo.label('idgrupo_evaluado'),
        GrupoEvaluado.nombre.label('grupo_evaluado'),
        DatosUnificados.puntuacion_evaluacion_promedio,
        DatosUnificados.puntuacion_evaluacion_mediana,
        DatosUnificados.grupo_puntuacion_evaluacion_promedio,
        DatosUnificados.grupo_puntuacion_evaluacion_mediana,
        DatosUnificados.grupo_puntuacion_confianza_promedio,
        DatosUnificados.grupo_puntuacion_confianza_mediana
    )\
        .select_from(DatosUnificados)\
        .join(GrupoEvaluador,
              DatosUnificados.grupo_evaluador_id == GrupoEvaluador.idgrupo)\
        .join(GrupoEvaluado,
              DatosUnificados.grupo_evaluado_id == GrupoEvaluado.idgrupo)\
        .join(FtEstudiante)\
        .filter(
            EnviarTarea.idactividad == idactividad)


# api end-points
@api.route('/fuzzy/apply-models')
class Fuzzy(Resource):
    @api.expect(activitySchema)
    @api.marshal_with(messageSchema)
    def post(self):
        payload = marshal(api.payload, activitySchema)
        applyModelsFuzzy(payload['idactividad'])
        return {'message': 'models apply done'}


@api.route('/fuzzy/data')
class FuzzyData(Resource):
    @api.expect(paginationParser)
    @api.marshal_with(paginationSchema)
    def get(self):
        args = paginationParser.parse_args()
        data = getData(args['idactividad'])

        del args['idactividad']

        if not args['per_page']:
            args['per_page'] = data.paginate(**args, error_out=False).total

        return data.paginate(**args, error_out=False)


if __name__ == '__main__':
    app.run(host='https://fuzzy-production.up.railway.app/', port='$PORT'}, debug=True)
