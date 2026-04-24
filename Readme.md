python -m venv venv
./venv/Script/activate
pip install pydantic


-----New Readme for User Login-------
The main 2 collections in my Midterm_with_User_Login DB are User and Application. However, applications are linked to user IDs, as can be seen in the ApplicationResponse class (includes an id parameter).
![alt text](image.png)\
![alt text](image-1.png)
The backend is linked to the login page of the frontend. My MongoDB connection string (to Atlas) is "mongodb+srv://chriss:VRf4H6BafmZbe8C@cluster0.acnynb2.mongodb.net/?appName=Cluster0", and beanie is used to initialize the connections.
![alt text](image-2.png)
Most code needed so that Applications are linked to user accounts (include the ID parameter) are included in routes.py. These include _app_owner_filter, _get_current_user, and _get_owned_applications; many of the backend CRUD functions/decorators include those 3 functions. Now, instead of saving application info in an in-memory database, it is saved in MongoDB. The _app_owner_filter function provides the owner ID corresponding to a specific user. For the User class, this is just the User ID. For the Application class, applications contain a "Owners" field, which includes an ID field that matches the User (ID) the application belongs to.
![alt text](image-4.png)
The function _get_current_user returns the current_user object that corresponds to a specific email (the current user object includes an ID, an email., and a pw). This object is frequently used when a new application is created, such as in the create_application function. "new_app = Application(Owner=current_user, **app.dict()) ensures that the owner of the new application being created is "current_user". If no email corresponds to the User we're trying to find, then the _get_current_user function returns "User no longer available".
![alt text](image-5.png)
![alt text](image-6.png)
the function _get_owned_application returns the Application that corresponds to a specific application id and current user (there might be 2 applications with the same app_id, but only one will correspond to the specific user current_user). This function is obviously used in the get_application function, and it directly returns the application returned by the get_owned_application function.
![alt text](image-8.png)
![alt text](image-7.png)
The upload_resume function also calls the _get_owned_application function. It does this to write the file path from the frontend to the resume_path parameter of the extracted application: application.resume_path = file_path. Using a MongoDB database, the updated application can be saved just by using "await application.save()"; there is no longer a need to commit anything. 
![alt text](image-9.png)
The get_applications function returns any applications corresponding to a specific user, but also allows a user to filter off status (Applied, rejected, interview, offer) and company. Of course, the first thing it does is use the _app_owner_filter button to return the ID corresponding to current_user (Any jobs corresponding to current_user will list this ID under their "Owners" parameter).
![alt text](image-10.png)
The update_Application function also uses _get_owned_application to find the application corresponding to a specific user and app_id. Then, once the specific application of interest is retrieved from the DB, its dictionary can be updated using app.set(updated_dictionary).
![alt text](image-12.png)
![alt text](image-11.png)
The delete_Application function has a format similar to the update_application function, except, instead of using app.set(dict), it uses app.delete(). It still needs to get the current user information using _get_current_user, and then get the application of interest using _get_owned_application(app_id, current_user).
![alt text](image-13.png)
Compared to before MongoDB and the user login featuers were implemented, the get_match_score function is almost exactly the same. The user and specific application are (like many of the previously discussed functions) obtained using _get_current_user and _get_owned_application. If either the resume or job posting link doesn't exist, no AI match score can be computed, and a 400 error is returned. From there, the texts from both are extracted, a score is computed using compute_match_score, and analyze_skill_gap is used to find the matched and missing skills (like before). These are all returned. 
![alt text](image-14.png)
The link betwee the Application class and the User class (via the owner field of the Application class) is achieved using "Owner: Link[User]" (this is a beanie feature).
![alt text](image-15.png)
The auth_routes.py, auth_utils.py, and authenticate.py programs are very similar to those in the "planners" repo provided in class. The _find_user_by_email function is used when someone creates an account; it makes sure someone doesn't register (sign up) with an account that already exists. It is also used when someone logs in to make sure the email the user tries to log in with actually exists in the MongoDB.
![alt text](image-16.png)
The register function is used when someone creates a new account. It first checks to mmake sure that the user doesn't already exist (using _find_user_by_email). Then, it obtains the email and password from the frontend, and it hashes the password. The user is then inserted into the database (with a corresponding ID, username, and hashed pw) using "await new_user.insert()". 
![alt text](image-17.png)
The login function first uses the _find_user_by_emmail function to make sure the email the user enters is actually in the DB (otherwise they need to sign up, not log in). Then, the verify_password function is used to make sure the plain pw the user enters matches the stored hash pw. 
![alt text](image-18.png)
Finally, the auth get("/me") function just simply takes in a user email, determines if it exists in the DB using _find_user_by_email, and returns it if it does.
![alt text](image-19.png)
Both functions in auth_utils.py are copied directly from the in class examples; both use the CryptContext function from bcrypt. pwd_context is used to hash the password in the hash_function; it is also used to compare the plain password a user enters to a hashed password.
![alt text](image-20.png)
The authenticate.py script comes from the planner repo. It takes in a token and passes it to verify_access_toke, where it is decoded, and the function makes sure the token data has an exp, email, and role. Then, a datetime object is created using exp, and a TokenData object is returned using the email, role, and exp_datetime. TokenData is returned from authenticate. for this project, the algorithm and secret KEY used to encode and decode are HS256 and dev-secret-change-me, respectively.
![alt text](image-21.png)
![alt text](image-22.png)
An access token is created using an email, role, and expiration date and time.All are added to "payload", which is then encoded into a token using the secret key and encoding algorithm.
Each User object in mongoDB includes an email, pw, and an ID (which again matches the ID stored in the Owners field for applications belonging to this user).
![alt text](image-23.png)
My login.html file is used for the login page; bootstrap is used for styling on this page. The login.html file then provides boxes for the user to enter his username and pw, and the user can choose to log in or register with those credentials. This login.html file is linked to main.js, since some of the functions in main.js are used to ensure the user is authenticated properly.
![alt text](image-24.png)
My main.js file (responsible for frontend logic) is mostly the same as before I added the login page; the only function responsible for ensuring the user is logged in properly and goes to the correct html page is the function checkAuth. It checks if the user is logged in, and if they are trying to access the login page or the main app page. For instance, loggedIn = localStorage.getItem("loggedIn") === "true" checks to see if the user is actually logged in. isLoginPage = path === "/" || path.endsWith("/login.html") and isAppPage = path.endsWith("/index.html") determine if the user is on the login page or the main app page (index.html). If the user is on the login page but is supposed to be logged in (entered the correct credentials and pressed log in), window.location.href is changed to index.html. Similarly, if the user is not supposed to be logged in (pressed log out) and they are currently on the app page, then the user is signed out using windows.location.href = "/" (root). On the main app page, "logged in as" + email is printed. Once a button is clicked on any html page (login page or main app page), "window.onload = checkAuth" is executed.
![alt text](image-25.png)
The function applyAuthHeader gets the access token and initializes that it will be used for authorization. It is used in the getAllApplications, deleteApplication, editApplication, createApplication, uploadResume, and getMatchScore functions.




---Old Readme for Midterm-----------------------------
![alt text](image-22.png)
![alt text](image-23.png)
The main purpose of the assignment was to build a web app using FASTAPI and demonstrate use of get/post/put/delete (CRUD) methods. The get method on my frontend, getAllApplications(), first obtains the company and status the user wants to restrict the search to. Then it establishes communication with the backend using xhr. Render applications creates the appDiv.innerHTML link, and the values in it are obtained from the backend using a xhr GET request.
![alt text](image.png)
The deleteApplications(id) function also first stablishes communication with backend. Then, it creates a DELETE request for the application of the specific id. 
![alt text](image-1.png)
My editApplications(id) function (for frontend) prompts the user for new values of company, role, status, priority, recruitmentinfo, and jobpostinglink. Once communication is made with backend, the list is refreshed, and a PUT request updates the values of all these parameters. a JSON string of all these values is sent to the backend. Then, getAllApplications() is called once more to refresh them.
![alt text](image-2.png)
The createApplication() function creates a new application by first initializing new values for company, role, status, priority, recruitmentinfo, resumeFile, and jobpostinglink. Then, a post request is sent to the backend with all these new values.
![alt text](image-3.png)
I also have an uploadResume(appId, file) function, which first takes the resume (file) and adds it to a file formData. a POST method is then created for the application of appId, and the resume is sent to the backend using xhr.send.
![alt text](image-4.png)
On the frontend, I also have a getMatchScore(appId) function, which simply obtains the match score, matched skills, and missing skills from the backend and prints them to the frontend. 
![alt text](image-5.png)
Finally, on the frontend, I have a function updateStatistics which computes the interViewRate and offerRate, keeps track of status and priority counts, and calls 2 associated functions which print bar and pi charts to the screen. The bar graph shows the # of jobs in each status category (applied, interview, offer, rejected), and the pi chart shows the % of jobs in each priority (high, medium, low).
![alt text](image-25.png)
![alt text](image-6.png)
![alt text](image-7.png)
On my backend, my main.py file initializes the FastAPI app, initializes CORS settings, connects backend to the frontend, creates database tables, and connects to my router in routes.py (responsible for CRUD methods). It is important that I import UploadFile from fastapi, since my web app involves uploading resumes.
![alt text](image-8.png)
My routes.py file includes all CRUD methods for the backend. For instance, it includes a create_application() post ethod, which creates a new app using the parameters defined in models.py, adds them to the database, commits the database, refreshes the database, and returns the new application to the frontend.
![alt text](image-9.png)
It also includes a post function for a specific appid, which basically allows a user to attach a resume to a pre-existing job application. First, it queries the database to find the appropriate application. Then, a file path is made based off the file sent to the function. the contents from the file sent to the function are written (binary) to the file path. Then, the file path is attached to application.resume_path (a parameter defined in models.py). Finally, the database is committed, and a relevant 'success' message is returned.
![alt text](image-10.png)
Of course, in the backend I also have a get all applications method, and at first it obtains all apps in the database. However, it has special query options for status and company. For instance, if a user specifies that status=applied and company=Boeing, the search will only return applications for which the user applied to Boeing. The results of the query are returned.
![alt text](image-11.png)
The backend also has a get method that returns a single application when the user enters in an acceptable appid (an HTTPException is returned if the user enters an invalid id). The application is returned.
![alt text](image-12.png)
On the backend, thre is also a put (update) method. Basically, a specific app_id is queried, and the values of company, role, status, priority, recruitmentinfo, and jobpostinglink returned from the frontend are updated in the backend (using updated_app.__ values). The database is committed and refreshed.
![alt text](image-26.png)
![alt text](image-13.png)
The backend also includes a delete_application function, which basically operates the same as the delete_todo method used in class. It queries the DB for the application of id app_id, and then, upon finding it, deletes it from the database.
![alt text](image-14.png)
My routes.py backend also includes a get_Match_Score function, whcih returns the match_score, matched_skills, and missing_skills to the frontend. Many of the functions it uses, such as extract_resume/job_text, compute_match_score, and analyze_skill_gap, are defined in ai_matcher.py. The method first checks that the application being queried (of id app_id) exists, that it has a resume, and that it has a job posting. If so, the texts from the resume and job posting are extracted (with non-important info being removed), and the skills/similarities in the 2 texts in skills_DB are compared using compute_match_score. Then, the specific texts included in both texts and those included in just the job posting are determined using the analyze_skill_gap function. Finally, the overall AI score, matched_skills, and missing_skills are returned.
![alt text](image-24.png)
![alt text](image-15.png)
My ai_matcher.py file contains the important methods that my get_Match_Score function in routes.py uses. For instance, it has functions to extract text from the resume and job description. My extract_job_text function extracts text from the specific URL and tries to match the URL to a linkedin job posting; if it fails, it just uses the original URL. Finally, the BeautifulSoup function creates a parse tree of the response.text, and this parse tree is returned. From there, methods can be used to search and extract content from the tree.
![alt text](image-16.png)
The clean_text function makes all text lowercase and reformats it for consistency. The extract_Skills function takes the text in "text" and sees which skills in SKILLS_DB it includes. These skills are then returned. The list of SKILLS_DB can be expanded as the web app is made to accommodate more types of resumes/job postings.
![alt text](image-17.png)
The compute_match_score function(resume_text, job_text) first cleans the text in the resume and job posting using the clean_text function. The job posting size is limited to the most useful material. A vectorizer is created to represent a matrix with the resume and job posting data, and it matches similar phrases (ex. "machine learning" and "computer vision"). Finally, the cosine_similarity function (the cosine_simularity function comes from the sklearn package) compares the resume and job posting texts from the vector and returns an array of matrices detailing how similar they are. The first element rperesents the overall similarity between the job posting and resume. I found these values to be strangely small in my testing, so for the sake of this web app, I multiplied it by 300 to make it more real-world.
![alt text](image-18.png)
My analyze_skill_gap(resume_text, job_text) first extracts skills from the resume and those in the job posting. Then, it compares both sets of skills, and the skills in both texts are referred to as matched_skills. Those only in the job posting are missing_skills. The skills are returned and used in the get_Match_Score function to be sent to the frontend.
![alt text](image-19.png)
My index.html file defines all the main parameter types used in my web app, including company, role, recruitmentinfo, resume file, jobpostinglink, and status. It includes the specific allowed values for 'status' and 'priority'. It includes the buttons for creating an application, searching a company, filtering by status, etc. It loads the bootstrap javascript bundle for interactive components. It also loads the chart.js library used to generate stats charts. It creates a Statistics section that shows total applications, interview rate, offer rate, a status bar chart, and a priority pi chart. It also has a link to main.js (CRUD methods for the frontend). It also has a link to style.css.
![alt text](image-20.png)
I just use an in-memory database (a list) for this project (I have DATABASE_URL = "sqlite:///:memory:"). My SessionLocal includes autocommit=false (if a CRUd method makes changes, it needs to commit them manually) and autoflush=false. Then, database.py includes a method called get_db(), which allows a CRUD method to open a local database session. when the CRUd method is using the database, the get_db() method just yields the database. Once the method is finished using it, the get_db() method closes the database.
![alt text](image-21.png)



python -m venv venv
.\venv\Scripts\Activate
pip install fastapi beanie uvicorn bcrypt pydantic[email] pydantic-sttings pyjwt python-multipart httpx pytest
uvicorn main:app --reload