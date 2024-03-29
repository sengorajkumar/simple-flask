from flask import Flask, request, url_for,render_template
from flask_pymongo import PyMongo
from flask_pymongo import ObjectId

app = Flask(__name__)
#Raj's dev atlas
#app.config["MONGO_URI"] = "mongodb+srv://my_mongodb_usr:peOEvgEyFN7mq3CD@cluster0-mjzfv.mongodb.net/griffindor?retryWrites=true&w=majority"
#Team's Atlas
app.config["MONGO_URI"] = "mongodb+srv://adminUser1:sSFbS6LILMsDnoni@cluster-gryffindor-cbtnr.gcp.mongodb.net/griffindor?retryWrites=true&w=majority"
mongo = PyMongo(app)

# App route to present create post form
@app.route("/create")
def create_post():
    return render_template("submit_post.html")

# API to retrieve all the posts
@app.route("/")
@app.route('/posts')
def display_all():
    ''' Retrieves all the posts available to display in home page'''
    posts = mongo.db.posts.find()
    post_list = []
    for post in posts:
        print(post['file_name'])
        post_list.append(post)
    return render_template("list_posts.html", posts=post_list)

# API to create a post to database
@app.route("/post", methods=['POST'])
def post():

    caption = request.form.get('caption').strip()
    tags = request.form.get('tags').split(",")
    user = request.form.get('user_id').strip()
    category = request.form.get('category').strip()

    #First insert the tags if its new tag otherwise reference the existing tag
    tags_coll = mongo.db.tags
    list_tag_ids = []
    for tag in tags:
        tag_value = tag.strip()
        value = tags_coll.update_one({"tag":tag_value},{"$set": {"tag":tag_value}},upsert=True)
        if value.upserted_id is None:
            existing_tag = tags_coll.find_one_or_404({"tag": tag_value})
            tag_id = existing_tag['_id']
        else:
            tag_id = ObjectId(value.upserted_id)
        list_tag_ids.append(ObjectId(tag_id))
    print("Tag Ids : " + str(list_tag_ids))

    #Do the same for category - This will be a defined list during later phases
    category_coll = mongo.db.categories
    value = category_coll.update_one({"category":category},{"$set": {"category":category}},upsert=True)
    if value.upserted_id is None:
        existing_cat = category_coll.find_one_or_404({"category": category})
        cat_id = ObjectId(existing_cat['_id'])
    else:
        cat_id = ObjectId(value.upserted_id)
    print("Category Id : " + str(cat_id))

    if 'picture_file' in request.files:
        picture_file_obj = request.files.get('picture_file')
        file_name = picture_file_obj.filename
        # Save the binary file to mongoDB
        mongo.save_file(file_name,picture_file_obj)
        # Insert a record to posts collection with reference to the saved picture file
        result = mongo.db.posts.insert_one(
            {'file_name': file_name,
             'user' : user,
             'caption': caption,
             'tags': request.form.get('tags'),
             'tag-ids' :list_tag_ids,
             'category-id' : cat_id
             })
    # Display the post once created
    dict_display = {"caption" : caption, "id":str(result.inserted_id),"tags":tags}
    return render_template("display_post.html", post=dict_display)

@app.route('/file/<filename>')
def file(filename):
    return mongo.send_file(filename)

@app.route('/show/<id>')
def show(id):
    post =  mongo.db.posts.find_one_or_404({"_id":ObjectId(id)})
    return mongo.send_file(post['file_name'])

@app.route('/post/<id>')
def display(id):
    print(id)
    post =  mongo.db.posts.find_one_or_404({"_id":ObjectId(id)})
    return f'''
        <h1>{post['caption']}</h1>
        <h3>{id}</h3>
        <h3>{post['tags']}</h3>
        <img src = "{url_for('file',filename=post['file_name'])}">
    '''

if __name__=='__main__':
    app.run(debug=1, host="127.0.0.1", port="9090")