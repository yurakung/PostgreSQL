import flask

import models
import forms
from flask import render_template, request, redirect, url_for, flash
from forms import NoteForm, TagForm
from models import Tag, db, Note



app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"

models.init_app(app)


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template(
        "index.html",
        notes=notes,
    )


@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        print("error", form.errors)
        return flask.render_template(
            "notes-create.html",
            form=form,
        )
    note = models.Note()
    form.populate_obj(note)
    note.tags = []

    db = models.db
    for tag_name in form.tags.data:
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
        )

        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)

        note.tags.append(tag)

    db.session.add(note)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    return flask.render_template(
        "tags-view.html",
        tag_name=tag_name,
        notes=notes,
    )

@app.route("/notes/edit/<int:note_id>", methods=["GET", "POST"])
def notes_edit(note_id):
    # ดึงข้อมูลโน๊ตที่ต้องการแก้ไขจากฐานข้อมูล
    note = Note.query.get(note_id)

    if not note:
        return "Note not found", 404
    
    form = NoteForm()

    if request.method == "POST":
        note.title = request.form["title"]
        note.description = request.form["description"]
        db.session.commit()

        return redirect(url_for("index"))

    return render_template("notes-edit.html", note=note, form=form)


@app.route("/notes/delete/<int:note_id>", methods=["GET", "POST"])
def notes_delete(note_id):
    note = Note.query.get(note_id)
    if not note:
        return "Note not found", 404
    
    form = NoteForm()
    if request.method == "POST":
        db.session.delete(note)
        db.session.commit()
        return redirect(url_for("index"))
    
    return render_template("notes-del.html", note=note, form=form)

@app.route("/tags/edit/<int:tag_id>", methods=["GET", "POST"])
def tags_edit(tag_id):

    tag = Tag.query.get(tag_id)

    form = TagForm()

    if not tag:
        return "tag not found", 404
    if request.method == "POST":
        tag.name = request.form["name"]
        db.session.commit()
        return redirect(url_for("index"))

    return render_template("tags-edit.html", tag=tag, form=form)

@app.route("/tags/delete/<int:tag_id>", methods=["GET", "POST"])
def tags_delete(tag_id):
    tag = Tag.query.get(tag_id)
    form = TagForm()

    if not tag:
        return "Tag not found", 404
    
    if request.method == "POST":
        referenced_notes = Note.query.filter(Note.tags.any(id=tag_id)).all()
        if referenced_notes:
            for note in referenced_notes:
                note.tags.remove(tag) 

            db.session.commit()
            db.session.delete(tag)
            db.session.commit()
            
            return redirect(url_for("index"))

    return render_template("tags-del.html", tag=tag, form=form)



if __name__ == "__main__":
    app.run(debug=True)
