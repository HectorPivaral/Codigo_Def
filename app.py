# -*- coding: utf-8 -*-
"""
Created on Fri Dec  6 17:47:23 2024

@author: aaron
"""

from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for


# Inicializar Flask y configurar la base de datos
app = Flask(__name__)
app.config.from_object('config.Config')

# Inicializar SQLAlchemy
db = SQLAlchemy(app)

# Modelos de las tablas
class RegistroOrdenes(db.Model):
    __tablename__ = 'registro_ordenes'
    id = db.Column(db.Integer, primary_key=True)
    nombre_orden = db.Column(db.String(255), nullable=False)
    fecha_entrega = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(50), nullable=False)
    fecha_actualizacion = db.Column(db.DateTime)

class Activacion(db.Model):
    __tablename__ = 'activacion'
    id = db.Column(db.Integer, primary_key=True)
    id_orden = db.Column(db.Integer, db.ForeignKey('registro_ordenes.id'), nullable=False)
    seleccionado = db.Column(db.Boolean, default=False)

class PendientesGestionadas(db.Model):
    __tablename__ = 'pendientes_gestionadas'
    id = db.Column(db.Integer, primary_key=True)
    id_orden = db.Column(db.Integer, db.ForeignKey('registro_ordenes.id'), nullable=False)
    fecha_gestion = db.Column(db.Date, nullable=False)


# Ruta principal
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/ordenes')
def ver_ordenes():
    # Mover las órdenes pendientes a la tabla Activación
    pendientes = RegistroOrdenes.query.filter_by(estado='Pendiente').all()
    for orden in pendientes:
        nueva_activacion = Activacion(id_orden=orden.id)
        db.session.add(nueva_activacion)
        db.session.commit()
    
    # Excluir las órdenes con estado "Pendiente" de la tabla principal
    ordenes = RegistroOrdenes.query.filter(RegistroOrdenes.estado != 'Pendiente').all()
    return render_template('ordenes.html', ordenes=ordenes)


@app.route('/crear', methods=['GET', 'POST'])
def crear_orden():
    if request.method == 'POST':
        # Obtener los datos del formulario
        nombre_orden = request.form['nombre_orden']
        fecha_entrega = request.form['fecha_entrega']
        estado = 'Pendiente'  # Estado inicial por defecto

        # Crear una nueva orden y guardarla en la base de datos
        nueva_orden = RegistroOrdenes(
            nombre_orden=nombre_orden,
            fecha_entrega=fecha_entrega,
            estado=estado
        )
        db.session.add(nueva_orden)
        db.session.commit()

        return redirect(url_for('ver_ordenes'))

    return render_template('crear.html')


@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_orden(id):
    # Obtener la orden por ID
    orden = RegistroOrdenes.query.get_or_404(id)
    
    if request.method == 'POST':
        # Actualizar los datos con los valores del formulario
        orden.nombre_orden = request.form['nombre_orden']
        orden.fecha_entrega = request.form['fecha_entrega']
        orden.estado = request.form['estado']
        db.session.commit()
        
        return redirect(url_for('ver_ordenes'))
    
    # Renderizar el formulario con los datos existentes
    return render_template('editar.html', orden=orden)


@app.route('/activacion', methods=['GET', 'POST'])
def ver_activacion():
    # Obtener todas las órdenes en la tabla Activación
    activaciones = db.session.query(Activacion, RegistroOrdenes).join(
        RegistroOrdenes, Activacion.id_orden == RegistroOrdenes.id).all()
    
    if request.method == 'POST':
        # Procesar órdenes seleccionadas para activar, rechazar, o gestionar
        seleccionadas = request.form.getlist('ordenes')
        accion = request.form['accion']
        
        for id_orden in seleccionadas:
            orden = RegistroOrdenes.query.get(int(id_orden))
            if accion == 'activar':
                orden.estado = 'Activado'
            elif accion == 'rechazar':
                orden.estado = 'Rechazado'
            elif accion == 'gestionar':
                orden.estado = 'Pendiente Gestionada'
            db.session.commit()

        # Eliminar de la tabla Activación
        Activacion.query.filter(Activacion.id_orden.in_(seleccionadas)).delete(synchronize_session=False)
        db.session.commit()

        return redirect(url_for('ver_activacion'))
    
    return render_template('activacion.html', activaciones=activaciones)


# Crear tablas (solo la primera vez)
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


'''
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
'''
