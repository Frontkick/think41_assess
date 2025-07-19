from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, exc
import re
from collections import defaultdict, deque

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spreadsheet.db'
db = SQLAlchemy(app)

class Spreadsheet(db.Model):
    id = db.Column(db.String, primary_key=True)
    cells = relationship('Cell', backref='spreadsheet', lazy=True)

class Cell(db.Model):
    id = db.Column(db.String, primary_key=True)
    spreadsheet_id = db.Column(db.String, db.ForeignKey('spreadsheet.id'), nullable=False)
    value = db.Column(db.String, nullable=True)
    formula_string = db.Column(db.String, nullable=True)
    precedents = relationship('CellDependency', backref='dependent_cell', lazy=True, foreign_keys='CellDependency.cell_id')
    dependents = relationship('CellDependency', backref='precedent_cell', lazy=True, foreign_keys='CellDependency.depends_on_id')

class CellDependency(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spreadsheet_id = db.Column(db.String, nullable=False)
    cell_id = db.Column(db.String, ForeignKey('cell.id'), nullable=False)
    depends_on_id = db.Column(db.String, ForeignKey('cell.id'), nullable=False)

def extract_cell_ids(formula):
    return re.findall(r'[A-Z]+[0-9]+', formula)

@app.route('/spreadsheets/<spreadsheet_id>/cells/<cell_id>/value', methods=['POST'])
def set_cell_value(spreadsheet_id, cell_id):
    data = request.get_json()
    value = data.get('value')
    cell = Cell.query.get(cell_id) or Cell(id=cell_id, spreadsheet_id=spreadsheet_id)
    cell.value = str(value)
    cell.formula_string = None
    CellDependency.query.filter_by(cell_id=cell_id).delete()
    db.session.add(cell)
    db.session.commit()
    return jsonify({"cell_id": cell_id, "value": value, "status": "value_set"})

@app.route('/spreadsheets/<spreadsheet_id>/cells/<cell_id>/formula', methods=['POST'])
def set_cell_formula(spreadsheet_id, cell_id):
    data = request.get_json()
    formula = data.get('formula_string')
    dependencies = extract_cell_ids(formula)
    cell = Cell.query.get(cell_id) or Cell(id=cell_id, spreadsheet_id=spreadsheet_id)
    cell.formula_string = formula
    cell.value = None
    CellDependency.query.filter_by(cell_id=cell_id).delete()
    for dep in dependencies:
        db.session.add(CellDependency(spreadsheet_id=spreadsheet_id, cell_id=cell_id, depends_on_id=dep))
    db.session.add(cell)
    db.session.commit()
    return jsonify({"cell_id": cell_id, "formula_string": formula, "status": "formula_set", "dependencies_identified": dependencies})

@app.route('/spreadsheets/<spreadsheet_id>/cells/<cell_id>', methods=['GET'])
def get_cell(spreadsheet_id, cell_id):
    cell = Cell.query.get(cell_id)
    if not cell:
        return jsonify({"error": "cell_not_found"}), 404
    return jsonify({"cell_id": cell_id, "value": cell.value, "formula_string": cell.formula_string})

@app.route('/spreadsheets/<spreadsheet_id>/cells/<cell_id>/dependents', methods=['GET'])
def get_dependents(spreadsheet_id, cell_id):
    dependents = CellDependency.query.filter_by(depends_on_id=cell_id).all()
    return jsonify([d.cell_id for d in dependents])

@app.route('/spreadsheets/<spreadsheet_id>/cells/<cell_id>/precedents', methods=['GET'])
def get_precedents(spreadsheet_id, cell_id):
    precedents = CellDependency.query.filter_by(cell_id=cell_id).all()
    return jsonify([p.depends_on_id for p in precedents])

@app.route('/spreadsheets/<spreadsheet_id>/recalculate-order')
def get_recalc_order(spreadsheet_id):
    start_cell = request.args.get('changed_cell_id')
    visited = set()
    stack = []
    temp_marks = set()
    adj = defaultdict(list)

    deps = CellDependency.query.filter_by(spreadsheet_id=spreadsheet_id).all()
    for dep in deps:
        adj[dep.depends_on_id].append(dep.cell_id)

    cycle = []
    def visit(node):
        if node in temp_marks:
            cycle.append(node)
            return False
        if node not in visited:
            temp_marks.add(node)
            for m in adj[node]:
                if not visit(m):
                    cycle.append(node)
                    return False
            temp_marks.remove(node)
            visited.add(node)
            stack.append(node)
        return True

    if not visit(start_cell):
        return jsonify({"error": "cycle_detected_involving_cells", "cells": list(set(cycle))}), 400
    return jsonify({"order": stack[::-1]})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # ✅ This now runs inside the app context
    app.run(debug=True)

