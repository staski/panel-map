// create a javascript import file from a directory containing media files (docs, images, texts)
// usage node crtimgsjs.js <media> directory/*, where media is any string
// will create an output (repeat export and import for every file in directory)
//
// import <media>filename from directory/filename.extension
// 
// export default {
//      <media>filename:<media>filename,
//      ...
// }
//
//  
const fs = require('fs');
const cheerio = require('cheerio');
const path = require('path');
const os = require('os');

const homedir = os.homedir();
    
const SRC = `${homedir}/panelMap`;
const DST = "./src";

var areaElements = [];
var allInstruments = [];

const imagesjs = `${DST}/images.js`;
const docsjs = `${DST}/docs.js`;
const textsjs = `${DST}/texts.js`;
const panelareasjs = `${DST}/panelAreas.js`;

const inputs = process.argv

// create the panelAreas.js file from the html image map
// areaElements array stores the areas for later use
const htmlFilePath = inputs[2] || `${SRC}/panelmap.html`;

console.log(`use map ${htmlFilePath}`);
// processHTMLFile returns the JSON string and fills the allInstruments array as a side-effect
var resultObjects = processHTMLFile(htmlFilePath);
resultObjects = resultObjects.slice(0,-1);

const str = `import images from './images';
import docs from './docs';
import texts from './texts';

var panelAreas = [
${resultObjects} 
];

export {
	panelAreas,
};`

try {
    fs.renameSync(panelareasjs, `${panelareasjs}.ori`);
} catch (err){
    console.log(err, " continues");
}
fs.appendFileSync(panelareasjs, str);



const imgdir = `${SRC}/images`;
console.log("images from " + imgdir);
const imglist = fs. readdirSync(imgdir);
console.log("imglist: ", imglist);

const docdir = `${SRC}/docs`;
console.log("docs from " + docdir);
const doclist = fs. readdirSync(docdir);
console.log("doclist: ", doclist);

var allImages = [];
var allDocs = [];

console.log("allinstruments: ", allInstruments);

try {
    fs.renameSync(imagesjs, `${imagesjs}.ori`);
} catch (err){
    console.log(err, `rename ${imagesjs}. continue`);
}

// include all images for which an instrument is available in the panel
imglist.forEach((value, index) => {
    var name = value.split('.').slice(0,-1).join('');
    if (!fs.existsSync(`${DST}/images`)){    
        fs.mkdirSync(`${DST}/images`);
        console.log(`created ${DST}/images`);
    }
    name = unifyNames(name);
    if (allInstruments.includes(name) || name === "cockpitpanel"){
        if (!allImages.includes(name)){
            allImages.push(name);
            fs.copyFileSync(`${imgdir}/${value}`,`${DST}/images/${value}`);
            console.log(`cp ${imgdir}/${value} to `,`${DST}/images/${value}`)
            fs.appendFileSync(imagesjs, `import img${name} from './images/${value}';\n`);
            console.log(`import img${name} from './images/${value}';`);
        } else {
            console.log(`skip duplicate ${name} - ${value}`);
        }
    }
});

// save old docs.js file
try {
    fs.renameSync(docsjs, `${docsjs}.ori`);
} catch (err){
    console.log(err, `rename ${docsjs}. continue`);
}

// include all docs for which an instrument is available in the panel
doclist.forEach((value, index) => {
    var name = value.split('.').slice(0,-1).join('');
    //var ext = value.split('.').slice(-1);
    if (!fs.existsSync(`${DST}/docs`)){    
        fs.mkdirSync(`${DST}/docs`);
        console.log(`created ${DST}/docs`);
    }
    name = unifyNames(name);
    if (allInstruments.includes(name)){
        if (!allDocs.includes(name)) {
            allDocs.push(name);
            fs.copyFileSync(`${docdir}/${value}`,`${DST}/docs/${value}`);
            console.log(`cp ${docdir}/${value} to `,`${DST}/docs/${value}`)
            fs.appendFileSync(docsjs, `import doc${name} from './docs/${value}';\n`);
            console.log(`import doc${name} from './docs/${value}';`);
        } else {
            console.log(`skip duplicate ${name} - ${value}`);
        }
    }
});

fs.appendFileSync(imagesjs, "\nexport default {\n");
allImages.forEach(element => {
    fs.appendFileSync(imagesjs, `  'img${element}':img${element},\n`);
});
fs.appendFileSync(imagesjs,"};\n");

fs.appendFileSync(docsjs, "\nexport default {\n");
allDocs.forEach(element => {
    fs.appendFileSync(docsjs, `  'doc${element}':doc${element},\n`);
});
fs.appendFileSync(docsjs,"};\n");

try {
    fs.renameSync(textsjs, `${textsjs}.ori`);
} catch (err){
    console.log(err, `rename ${textsjs}. continue`);
}
fs.appendFileSync(textsjs, "\nexport default {\n");
allImages.forEach(element => {
    fs.appendFileSync(textsjs,`  'title${element}':"${element}",\n`);
    fs.appendFileSync(textsjs,`  'text${element}':"${element}",\n`);
});
fs.appendFileSync(textsjs,"};\n");



function unifyNames(text) {
    return text.toLowerCase()
        .replace(/[-_\s.]+(.)?/g, (_, c) => c ? c: '');
}

 function camelize(text) {
    const a = text.toLowerCase()
        .replace(/[-_\s.]+(.)?/g, (_, c) => c ? c.toUpperCase() : '');
    return a.substring(0, 1).toLowerCase() + a.substring(1);
}
 
function convertToString(areaElement, idx) {
    const n1 = areaElement.attr('title') || '';
    const shape = areaElement.attr('shape') || '';
    const coords = areaElement.attr('coords').split(',').map(Number) || [];
    const stridx = String(idx);
    const name = camelize(n1);
  
    var lobj = "{\n\tname:\t'" + name + "',\n" +
      "\tshape:\t'" + shape +"',\n" +  
      "\tcoords:\t[" + coords + "],\n" +
      "\tid:\t'" + stridx + "',\n" +
      "\timg:\timages.img" + name + ",\n" +
      "\ttitle:\ttexts.title" + name + ",\n" +
      "\thref:\tdocs.doc" + name + ",\n" +
      "\ttext:\ttexts.text" + name + "\n" + "},\n"
    return lobj;
  }
  
  
  function processHTMLFile(filePath) {
    const htmlContent = fs.readFileSync(filePath, 'utf-8');
    const $ = cheerio.load(htmlContent);

    areaElements = $('area');
    var resStr = "";
    areaElements.map((index, element) => {
      resStr = resStr + convertToString($(element), index);
    });  
    
    areaElements.map((index, element) => {
        allInstruments.push($(element).attr('title'));
        console.log("device: ", $(element).attr('title'));
    });
    console.log("allinstruments: ", allInstruments);
    return resStr;
  }
  
  function getFilePath(filename){
    const os = require("os");
    const homedir = os.homedir();
    console.log(" check",  `${homedir}/.panelMap/${filename}`);
    if (fs.existsSync(`${homedir}/.panelMap/${filename}`)){
        return `${homedir}/.panelMap/${filename}`;
    } else {
        return `./src/${filename}`;    }
    
  }