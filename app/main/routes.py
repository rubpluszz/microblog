#-*- coding: utf-8 -*-
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from guess_language import guess_language
from app import db
from app.models import User, Post, Comments, likes_table_comments, PrivateMessages
from app.translate import translate
from app.main import bp
from app.main.forms import PostForm, CommentsForm, EmptyForm, MessageForm

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@bp.route('/blog', methods=['GET', 'POST'])
def blog():
    form = PostForm()
    user = current_user
    if form.validate_on_submit():
        language = guess_language(form.post.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        post = Post(body = form.post.data, 
                    title = form.post_title.data,
                    description = form.description.data,
                    title_image = form.title_image.data,
                    language = language,
                    section = form.post_section.data)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('main.blog'))
    selected_posts = db.session.query(Post).filter(Post.selected_posts==1).all()
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.blog', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.blog', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='PluszzBlog',
                           posts=posts, selected_posts=selected_posts, next_url=next_url,
                           prev_url=prev_url, user=user, form=form)


@bp.route('/post/<post_id>', methods=['GET', 'POST'])
def post(post_id):
    form = CommentsForm()
    user = current_user
    post = Post.query.filter_by(id=post_id).first()
    selected_posts = db.session.query(Post).filter(Post.selected_posts==1).all()
    if form.validate_on_submit() and form.comment.data!=None:
        comment = Comments(body=form.comment.data, user_id=user.id, post_id=post.id)
        db.session.add(comment)
        db.session.commit()
        form.comment.data = ''#clear comment field
        return redirect('{}'.format(str(post_id)))
    page = request.args.get('page', 1, type=int)
    comments = Comments.query.filter_by(post_id=post_id).order_by(Comments.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.post',post_id=post_id, page=comments.next_num) if comments.has_next else None
    prev_url = url_for('main.post',post_id=post_id, page=comments.prev_num) if comments.has_prev else None
    locale = get_locale()
    post.vievs_upper()
    db.session.commit()
    return render_template('post.html', User=User, Comments=Comments, likes_table_comments=likes_table_comments, 
                            title=post.title, post=post, next_url=next_url, prev_url=prev_url, form=form, db=db, 
                            comments=comments, locale=locale, user=user, selected_posts=selected_posts)

@bp.route('/liked_post/<int:post_id>')
@login_required
def like_post( post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    current_user.like_this_post(post)
    db.session.commit()
    return redirect(url_for('main.post', post_id=post_id))    


@bp.route('/dislike_comment/<int:post_id>')
@login_required
def dislike_post( post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    current_user.dislike_this_post(post)
    db.session.commit()
    return redirect(url_for('main.post', post_id=post_id)) 


@bp.route('/like_comment/<int:comment_id>/<int:post_id>')
@login_required
def like_comment(comment_id, post_id):
    comment = Comments.query.filter_by(id=comment_id).first_or_404()
    current_user.like_this_comments(comment)
    db.session.commit()
    return redirect(url_for('main.post', post_id=post_id))    


@bp.route('/dislike_comment/<int:comment_id>/<int:post_id>')
@login_required
def dislike_comment(comment_id, post_id):
    comment = Comments.query.filter_by(id=comment_id).first_or_404()
    current_user.dislike_this_comments(comment)
    db.session.commit()
    return redirect(url_for('main.post', post_id=post_id)) 
  

@bp.route("/about")
def about():
    selected_posts = db.session.query(Post).filter(Post.selected_posts==1).all()
    return render_template('about.html', selected_posts=selected_posts)

@bp.route("/projects")
def projects():
    selected_posts = db.session.query(Post).filter(Post.selected_posts==1).all()
    return render_template('projects.html', selected_posts=selected_posts)

@bp.route("/section")
def section():
    selected_posts = db.session.query(Post).filter(Post.selected_posts==1).all()
    return render_template('section.html', selected_posts=selected_posts)

@bp.route("/cooperation")
def cooperation():
    selected_posts = db.session.query(Post).filter(Post.selected_posts==1).all()
    return render_template('coperation.html', selected_posts=selected_posts)

@bp.route('/user/<username>')
@bp.route('/user/<username>/<category>')
@login_required
def user(username, category="_favorite_posts"):
    user = User.query.filter_by(username=username).first_or_404()
    form = EmptyForm()
    page = request.args.get('page', 1, type=int)
    page_to_vievs = category+'.html'
    if category=="_favorite_posts":
        liked_posts = user.liked_posts().paginate(page, current_app.config['POSTS_PER_PAGE'], False)
        next_url = url_for('main.blog', page=liked_posts.next_num) if liked_posts.has_next else None
        prev_url = url_for('main.blog', page=liked_posts.prev_num) if liked_posts.has_prev else None
    if category=='_recomendation':
        liked_posts = db.session.query(Post).filter(Post.selected_posts==1).all()
        next_url, prev_url = None, None 
    if category =='_read_later':
        liked_posts = user.to_read_later().paginate(page, current_app.config['POSTS_PER_PAGE'], False)
        next_url = url_for('main.blog', page=liked_posts.next_num) if liked_posts.has_next else None
        prev_url = url_for('main.blog', page=liked_posts.prev_num) if liked_posts.has_prev else None
    return render_template('user_page.html', page_to_vievs=page_to_vievs, Comments=Comments, user=user,
                           form=form ,liked_posts=liked_posts, prev_url=prev_url, next_url=next_url)





@bp.route("/messages")
@login_required
def messages():
    user = current_user
    current_user.last_message_read_time = datetime.utcnow()
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.message_received.order_by(
        PrivateMessages.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.messages', page=messages.next_num) if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) if messages.has_prev else None
    return render_template('user_page.html',page_to_vievs='_messages.html', messages=messages.items, 
                            user=user, next_url=next_url, prev_url=prev_url, User=User)




@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = PrivateMessages(sender=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        db.session.commit()
        flash(_('Your message has been sent.'))
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_message.html', title=_('Send Message'),
                           form=form, recipient=recipient)