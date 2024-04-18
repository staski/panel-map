const cheerio = require('cheerio');
const fs = require('fs');
var areaElements = [];

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

  return resStr;
}

const inputs = process.argv

const htmlFilePath = inputs[2] || "";
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

console.log(str);
