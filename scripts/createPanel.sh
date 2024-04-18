#!/bin/bash
node ./scripts/createPanel.sh panelMap.html
node ./scripts/crtimgsjs.js img ./imgs/* > imgs.js
node ./scripts/crtimgsjs.js doc ./docs/* > docs.js
