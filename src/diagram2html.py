## take the javascript diagram files, and generate standalone html files from them
import os.path

header = """ <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Digiaktiv Model Processing Demo</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-ka7Sk0Gln4gmtz2MlQnikT1wXgYsOg+OMhuP+IlRH9sENBO0LRn5q+8nbTov4+1p" crossorigin="anonymous"></script>
</head>
<body>

    <div class = "w-120 container-fluid">
        <h3 id = "title"> Title of the diagram </h3>
        <div class="w-75" id="paper"> </div>
    </div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/lodash.js/4.17.21/lodash.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/backbone.js/1.4.0/backbone.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jointjs/3.5.5/joint.js"></script>

<script>"""

footer = """ </script>
</body> """

def makeHtml(jsfile = "C:/Users/BuruzsA/PycharmProjects/diagram2model/webapp/static/uploads/diagrams/Beispielschemen_digiaktiv_p5.js",
             outdir = "C:/Users/BuruzsA/PycharmProjects/diagram2model/webapp/static/uploads/diagramHTML/"):
    f = open(jsfile, "r")
    jsscript = f.read()
    htmltext = header + jsscript +footer
    outfilename = os.path.basename(jsfile).replace("js", "html")
    outfile = os.path.join(outdir, outfilename)
    with open(outfile, "w") as text_file:
        text_file.write(htmltext)

if __name__ == "__main__":
    diagpath = "C:/Users/BuruzsA/PycharmProjects/diagram2model/webapp/static/uploads/diagrams/"
    jsfilens = os.listdir(diagpath)
    for jsfile in jsfilens:
        jsfilep = os.path.join(diagpath, jsfile)
        makeHtml(jsfilep)


