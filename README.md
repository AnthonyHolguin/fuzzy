# api-fuzzy

## Python setup

### Linux

```bash
python -m venv pyenv
ln -sf pyenv/bin/activate .
source activate
pip install -U pip wheel
pip install -r requirements.txt
```

### Windows

```bash
pip install -U pip wheel
pip install -r requirements.txt
```

## PostgreSQL url setup

```txt
postgresql+psycopg2://user:password@host:port/dbname
```

Update table `evaluacion`

```sql
ALTER TABLE public.evaluacion ADD puntuacion_evaluacion numeric NULL;
ALTER TABLE public.evaluacion ADD puntuacion_confianza numeric NULL;

ALTER TABLE public.evaluacion ADD CONSTRAINT fk_evaluacion_ft_estudiante
    FOREIGN KEY (idestudiante) REFERENCES public.ft_estudiante(idestudiante);

-- DROP TABLE IF EXISTS public.datos_unificados;
CREATE TABLE public.datos_unificados
(
    iddatounificado character varying DEFAULT gen_random_uuid(),
    idactividad integer NOT NULL,
    grupo_evaluador_id integer NOT NULL,
    grupo_evaluado_id integer NOT NULL,
    estudianteid character varying NOT NULL,
    puntuacion_evaluacion_promedio numeric NOT NULL,
    puntuacion_evaluacion_mediana numeric NOT NULL,
    grupo_puntuacion_evaluacion_promedio numeric,
    grupo_puntuacion_evaluacion_mediana numeric,
	grupo_puntuacion_confianza_promedio numeric,
	grupo_puntuacion_confianza_mediana numeric,
    PRIMARY KEY (iddatounificado),
    FOREIGN KEY (idactividad)
        REFERENCES public.actividad (idactividad) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID,
    FOREIGN KEY (grupo_evaluador_id)
        REFERENCES public.grupo (idgrupo) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID,
    FOREIGN KEY (grupo_evaluado_id)
        REFERENCES public.grupo (idgrupo) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID,
    FOREIGN KEY (estudianteid)
        REFERENCES public.ft_estudiante (idestudiante) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
);

ALTER TABLE IF EXISTS public.datos_unificados
    OWNER to postgres;


-- validation query
select	datos_unificados.idactividad,
	grupo_evaluador.idgrupo, grupo_evaluador.nombre,
	ft_estudiante.rol, ft_estudiante.idestudiante,
	ft_estudiante.apellido1||' '||ft_estudiante.apellido2||' '||ft_estudiante.nombres as estudiante,
	grupo_evaluado.idgrupo, grupo_evaluado.nombre,
	datos_unificados.puntuacion_evaluacion_promedio,
	datos_unificados.puntuacion_evaluacion_mediana,
	datos_unificados.grupo_puntuacion_evaluacion_promedio,
	datos_unificados.grupo_puntuacion_evaluacion_mediana
from	datos_unificados
	inner join grupo as grupo_evaluador on grupo_evaluador.idgrupo = datos_unificados.grupo_evaluador_id
	inner join grupo as grupo_evaluado on grupo_evaluado.idgrupo = datos_unificados.grupo_evaluado_id
	inner join ft_estudiante ON ft_estudiante.idestudiante = datos_unificados.estudianteid
order by datos_unificados.idactividad, grupo_evaluador.idgrupo,
	ft_estudiante.rol, ft_estudiante.idestudiante, grupo_evaluado.idgrupo

-- 1
select	datos_unificados.idactividad,
	grupo_evaluador.idgrupo, grupo_evaluador.nombre,
	ft_estudiante.rol, ft_estudiante.idestudiante,
	ft_estudiante.apellido1||' '||ft_estudiante.apellido2||' '||ft_estudiante.nombres as estudiante,
	grupo_evaluado.idgrupo, grupo_evaluado.nombre,
	datos_unificados.puntuacion_evaluacion_promedio,
	datos_unificados.puntuacion_evaluacion_mediana,
	datos_unificados.grupo_puntuacion_evaluacion_promedio,
	datos_unificados.grupo_puntuacion_evaluacion_mediana,
	evaluacion.*,
	tipo_agrupamiento.idgrupo
from	datos_unificados
	inner join grupo as grupo_evaluador on grupo_evaluador.idgrupo = datos_unificados.grupo_evaluador_id
	inner join grupo as grupo_evaluado on grupo_evaluado.idgrupo = datos_unificados.grupo_evaluado_id
	inner join ft_estudiante ON ft_estudiante.idestudiante = datos_unificados.estudianteid
	inner join evaluacion ON evaluacion.idestudiante = ft_estudiante.idestudiante
	inner join asignacion_evaluacion on evaluacion.idasignacion_evaluacion = asignacion_evaluacion.idasignacion_evaluacion
	inner join tipo_agrupamiento on tipo_agrupamiento.idtipo_agrupamiento = asignacion_evaluacion.idtipo_agrupamiento_evaluador
		and tipo_agrupamiento.idgrupo = datos_unificados.grupo_evaluado_id
	inner join enviar_tarea on evaluacion.idenviar_tarea = enviar_tarea.idenviar_tarea
where	evaluacion.idevaluacion_evaluador is not null
	and enviar_tarea.idactividad = 103
order by datos_unificados.idactividad, grupo_evaluador.idgrupo,
	ft_estudiante.rol, ft_estudiante.idestudiante, grupo_evaluado.idgrupo;

-- 2
select	tipo_agrupamiento.idgrupo as grevaluador,
	evaluado.idgrupo as grevaluado, evaluacion.*
from	evaluacion
	inner join enviar_tarea on evaluacion.idenviar_tarea = enviar_tarea.idenviar_tarea
	inner join asignacion_evaluacion on evaluacion.idasignacion_evaluacion = asignacion_evaluacion.idasignacion_evaluacion
	inner join tipo_agrupamiento on tipo_agrupamiento.idtipo_agrupamiento = asignacion_evaluacion.idtipo_agrupamiento_evaluador
	inner join tipo_agrupamiento as evaluado on evaluado.idtipo_agrupamiento = asignacion_evaluacion.idtipo_agrupamiento_evaluado
where	idestudiante = '1312440256'
	and idevaluacion_evaluador is not null
	and enviar_tarea.idactividad = 103;
	
	
select	tipo_agrupamiento.idgrupo as grevaluador,
	evaluado.idgrupo as grevaluado, evaluacion.*
from	evaluacion
	inner join enviar_tarea on evaluacion.idenviar_tarea = enviar_tarea.idenviar_tarea
	inner join asignacion_evaluacion on evaluacion.idasignacion_evaluacion = asignacion_evaluacion.idasignacion_evaluacion
	inner join tipo_agrupamiento on tipo_agrupamiento.idtipo_agrupamiento = asignacion_evaluacion.idtipo_agrupamiento_evaluador
	inner join tipo_agrupamiento as evaluado on evaluado.idtipo_agrupamiento = asignacion_evaluacion.idtipo_agrupamiento_evaluado
where	idestudiante = '1312440256'
	and idevaluacion_evaluador is null
	and enviar_tarea.idactividad = 103;
```

## Run

```bash
python app.py
```

Open http://localhost:5000

## Notas

- Grupos sin docente
- Docentes con grupo evaluador
