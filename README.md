# focus_scraping

Pull this repo, and edit the template.yaml variables. Once done, edit "app.py" in the ./src/ directory and the dockerfile. Add your aws credentials replacing the ${access key & secret key} with your information then perform these actions in CL
to build docker container, and test locally. Once it compiles locally and performs all that you wish, move forward with the final CL statement. 

## CL statements

```bash
# Build Docker Container and Images
sam build

# Test function locally
sam local invoke

# Deploy Code to AWS Lambda
sam deploy --guided
```




