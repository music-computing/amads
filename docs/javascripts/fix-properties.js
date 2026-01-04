// This program patches mkdocs output in several ways.
//
// Mainly, it changes font sizes to make them more uniform.
//
// It also finds all properties and puts summaries for them
// along with Parameters, Attributes, and Methods summaries
// right after start of each class description.
//
// It also changes the section heading "Attributes" to
// "Properties" since it is the properties that get listed
// in the detailed descriptions (before "Functions", which
// appear below "Attributes"). This change to Properties
// is meant to work with the redefinition in extras.css
// of code.doc-symbol-attribute::after, where the content
// is changed from "attr" to "prop" so that "prop" appears
// before each property description.

document.addEventListener("DOMContentLoaded", function() {
    // Function to reformat summary items to use h3 style
    function reformatSummaryItems(listItems) {
        listItems.forEach(li => {
            // Skip if already has h3
            if (li.querySelector('h3')) return;
            
            // Get the first code element (the name)
            let firstCode = li.querySelector('code');
            if (!firstCode) return;
            
            // Get everything after the name
            const restOfContent = [];
            const firstCodeParent = firstCode.parentNode;
            if (firstCodeParent.tagName == "B") {
                firstCode = firstCodeParent;
            }
            let node = firstCode.nextSibling;
            while (node) {
                restOfContent.push(node);
                node = node.nextSibling;
            }
            
            // Clear the li
            li.innerHTML = '';
            li.className = 'doc-section-item field-body';
            
            // Create h3 with name only
            const h3 = document.createElement('h3');
            h3.className = 'doc doc-heading doc-heading-parameter';
            
            const nameB = document.createElement('b');
            nameB.appendChild(firstCode);
            h3.appendChild(nameB);
            
            li.appendChild(h3);
            
            // Add back the rest of the content
            restOfContent.forEach(node => {
                li.appendChild(node.cloneNode(true));
            });
        });
    }
    
    // Find all class documentation sections
    document.querySelectorAll('.doc-class').forEach(classDoc => {
        const summarySection = classDoc.querySelector('.doc-contents');
        if (!summarySection) return;
        
        // Reformat Attributes
        const attributesHeading = Array.from(summarySection.querySelectorAll('p > .doc-section-title'))
            .find(title => title.textContent.trim() === 'Attributes:');
        if (attributesHeading) {
            const attributesList = attributesHeading.parentNode.nextElementSibling;
            if (attributesList) {
                const listItems = attributesList.querySelectorAll('li');
                reformatSummaryItems(listItems);
            }
        }
        
        // Reformat Methods
        const methodsHeading = Array.from(summarySection.querySelectorAll('p > .doc-section-title'))
            .find(title => title.textContent.trim() === 'Methods:');
        if (methodsHeading) {
            const methodsList = methodsHeading.parentNode.nextElementSibling;
            if (methodsList) {
                const listItems = methodsList.querySelectorAll('li');
                reformatSummaryItems(listItems);
            }
        }
        
        // Now add Properties section (if methods exist)
        if (!methodsHeading) return;
        
        // Find all properties in the detailed documentation
        const properties = [];
        classDoc.querySelectorAll('.doc-attribute, .doc-property').forEach(prop => {
            const nameElement = prop.querySelector('.doc-heading');
            
            if (nameElement) {
                let fullText = nameElement.textContent.trim();
                fullText = fullText.replace('¶', '').trim();
                let parts = fullText.split('.');
                let lastPart = parts[parts.length - 1];
                let name = lastPart.split(/\s+/)[0].trim();
                
                // Get the property's ID for linking
                let propId = nameElement.id;
                
                let propType = '';
                const signatureElement = prop.querySelector('.doc-signature');
                if (signatureElement) {
                    const sigText = signatureElement.textContent;
                    const typeMatch = sigText.match(/:\s*([^=]+?)(?:\s*=|$)/);
                    if (typeMatch) {
                        propType = typeMatch[1].trim();
                    }
                }
                
                const descElement = prop.querySelector('.doc-contents > p');
                let desc = '';
                if (descElement) {
                    // Get the full text of the first paragraph (summary)
                    desc = descElement.textContent.trim();
                }
                
                if (name && name.length > 0) {
                    properties.push({ name, type: propType, desc, id: propId });
                }
            }
        });
        
        if (properties.length === 0) return;
        
        // Create Properties section
        const propertiesParagraph = document.createElement('p');
        
        const propertiesTitle = document.createElement('span');
        propertiesTitle.className = 'doc-section-title';
        propertiesTitle.textContent = 'Properties:';
        propertiesParagraph.appendChild(propertiesTitle);
        
        const propertiesList = document.createElement('ul');
        properties.forEach(prop => {
            const li = document.createElement('li');
            li.className = 'doc-section-item field-body';
            
            // Create h3 with property name only
            const h3 = document.createElement('h3');
            h3.className = 'doc doc-heading doc-heading-parameter';
            
            const nameB = document.createElement('b');
            const nameCode = document.createElement('code');
            nameCode.textContent = prop.name;
            
            // Wrap the property name in a link if we have an ID
            if (prop.id) {
                const link = document.createElement('a');
                link.href = '#' + prop.id;
                link.appendChild(nameCode);
                nameB.appendChild(link);
            } else {
                nameB.appendChild(nameCode);
            }
            
            h3.appendChild(nameB);
            
            li.appendChild(h3);
            
            // Add type in parentheses AFTER the h3
            if (prop.type) {
                li.appendChild(document.createTextNode(' ('));
                const typeCode = document.createElement('code');
                typeCode.textContent = prop.type;
                li.appendChild(typeCode);
                li.appendChild(document.createTextNode(')'));
            }
            
            // Add description
            if (prop.desc) {
                li.appendChild(document.createTextNode(' — '));
                const descDiv = document.createElement('div');
                descDiv.className = 'doc-md-description';
                const descP = document.createElement('p');
                descP.textContent = prop.desc;
                descDiv.appendChild(descP);
                li.appendChild(descDiv);
            }
            
            propertiesList.appendChild(li);
        });
        propertiesParagraph.appendChild(propertiesList);
        
        // Insert Properties section right before Methods section
        methodsHeading.parentElement.parentNode.insertBefore(
            propertiesParagraph, 
            methodsHeading.parentElement
        );
    });

    const h3elements = document.querySelectorAll('h3')
    h3elements.forEach(h3elem => {
        if (h3elem.textContent.trim().startsWith("Attributes")) {
            h3elem.firstChild.textContent = "Properties";
        }});
});
