# Image Processing

This is an image processing application that is based on FastAPI for backend and Python Imaging Library or Pillow for image class and functions. It uses MongoDB for user and image data. Its endpoints are secured using JWT authentication.

To use this application, 
1. Create a **.env** file containing the field and values required at app/core/config.
2. Configure the MongoDSN at app/core/config.
3. Run **fastapi dev**.
4. Open the OpenAPI documentation on your browser.
5. Sign up using the **/users/create** path.
6. Sign in using the authorize button at the top of the OpenAPI documentation.

This project is a work in progress.
