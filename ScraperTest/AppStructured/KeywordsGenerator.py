import json
def generate(companyInfo:list):
    data = None
    with open("AppStructured/keywords_template.json","r") as f:
       data = json.loads(f.read())
    for x in companyInfo:
        data["companyKeywords"].append(x)
    with open("AppStructured/keywords.json","w") as f:
        f.write(json.dumps(data))

if __name__ == "__main__":
    generate(["ciao"])
