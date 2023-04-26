 var namespace = joint.shapes;

        document.getElementById('title').innerText = "page 1"

        var graph = new joint.dia.Graph({}, { cellNamespace: namespace });

        var paper = new joint.dia.Paper({
            el: document.getElementById('paper'),
            model: graph,
            width: 800,
            height: 800,
            gridSize: 1,
            cellViewNamespace: namespace
        });

        var rect = new joint.shapes.standard.Rectangle();
        rect.position(100, 100);
        rect.resize(70, 40);
        rect.attr({
            body: {
                fill: 'blue'
            },
            label: {
                text: 'Hello',
                fill: '#AAAAAA'
            }
        });
        // rect.addTo(graph);

        var ellipse = new joint.shapes.standard.Ellipse();
        ellipse.resize(100, 70);
        ellipse.position(100, 100);
        ellipse.attr('label/text', 'Ellipse');
        ellipse.attr('body/fill', 'lightblue');


    
        var hn0 = ellipse.clone();
        hn0.translate( 0, 0); // position 100 pixels to left
        hn0.attr('label/text', '- P P E 0 0 1 :' );
        hn0.addTo(graph);
    
        var hn1 = ellipse.clone();
        hn1.translate( 100, 0); // position 100 pixels to left
        hn1.attr('label/text', '- T V L 0 0 1 :' );
        hn1.addTo(graph);
    
        var hn2 = ellipse.clone();
        hn2.translate( 200, 0); // position 100 pixels to left
        hn2.attr('label/text', '- V E N 0 0 1 : B :' );
        hn2.addTo(graph);
    
        var hn3 = ellipse.clone();
        hn3.translate( 300, 0); // position 100 pixels to left
        hn3.attr('label/text', '- T R L 0 0 1 :' );
        hn3.addTo(graph);
    

    
        var tl0 = rect.clone();
        tl0.resize(90, 120);
        tl0.translate( 0, 250); // position 100 pixels to left
        tl0.attr('label/text', '<Umwälzpumpe >\nSchaltbefehl\n SB\n\n|| BA ||' );
         
        tl0.addTo(graph);
        /// add the links:
        var link = new joint.shapes.standard.Link();
        link.source(hn0);
        link.target(tl0);
        link.addTo(graph);
    
        var tl1 = rect.clone();
        tl1.resize(90, 120);
        tl1.translate( 100, 250); // position 100 pixels to left
        tl1.attr('label/text', '<VL-Temperatursensor >\nMesswert\nMW\nAE\n\n|| ||' );
         
        tl1.addTo(graph);
        /// add the links:
        var link = new joint.shapes.standard.Link();
        link.source(hn1);
        link.target(tl1);
        link.addTo(graph);
    
        var tl2 = rect.clone();
        tl2.resize(90, 120);
        tl2.translate( 200, 250); // position 100 pixels to left
        tl2.attr('label/text', '<Einwegregelventil >\nHandmeldung Analog (VBE)\n BB\n\n|| BE ||' );
         
            tl2.resize(120, 140);
         
        tl2.addTo(graph);
        /// add the links:
        var link = new joint.shapes.standard.Link();
        link.source(hn2);
        link.target(tl2);
        link.addTo(graph);
    
        var tl3 = rect.clone();
        tl3.resize(90, 120);
        tl3.translate( 300, 250); // position 100 pixels to left
        tl3.attr('label/text', '<RL-Temperatursensor >\nMesswert\nMW\nAE\n\n|| ||' );
         
        tl3.addTo(graph);
        /// add the links:
        var link = new joint.shapes.standard.Link();
        link.source(hn3);
        link.target(tl3);
        link.addTo(graph);
    

    
        var cbl0 = rect.clone();
        cbl0.translate( 533.6842105263157, 307.14285714285603 ); // position 100 pixels to left
        cbl0.attr('label/text', 'Cont_0: MAX' );
        cbl0.attr('body/fill', '#11BB11');
        cbl0.attr('label/fill', '#441155');
        cbl0.resize(50,40);
        cbl0.addTo(graph);
    
        var cbl1 = rect.clone();
        cbl1.translate( 211.57894736842104, 475.7142857142858 ); // position 100 pixels to left
        cbl1.attr('label/text', 'Cont_1: -D02' );
        cbl1.attr('body/fill', '#11BB11');
        cbl1.attr('label/fill', '#441155');
        cbl1.resize(50,40);
        cbl1.addTo(graph);
    
        var cbl2 = rect.clone();
        cbl2.translate( 556.3157894736843, 475.7142857142858 ); // position 100 pixels to left
        cbl2.attr('label/text', 'Cont_2: -D03' );
        cbl2.attr('body/fill', '#11BB11');
        cbl2.attr('label/fill', '#441155');
        cbl2.resize(50,40);
        cbl2.addTo(graph);
    
        var cbl3 = rect.clone();
        cbl3.translate( 10.0, 550.0 ); // position 100 pixels to left
        cbl3.attr('label/text', 'Cont_3: -D04' );
        cbl3.attr('body/fill', '#11BB11');
        cbl3.attr('label/fill', '#441155');
        cbl3.resize(50,40);
        cbl3.addTo(graph);
    

    
        var link = new joint.shapes.standard.Link();
        
            link.source(tl1);
            link.target(cbl1);
        
        link.connector('rounded', { radius: 20 });
        link.connector('smooth');
        link.addTo(graph);
    
        var link = new joint.shapes.standard.Link();
         
            link.source(cbl0);
            link.target(tl2);
        
        link.connector('rounded', { radius: 20 });
        link.connector('smooth');
        link.addTo(graph);
    
        var link = new joint.shapes.standard.Link();
         
            link.source(cbl0);
            link.target(tl2);
        
        link.connector('rounded', { radius: 20 });
        link.connector('smooth');
        link.addTo(graph);
    
        var link = new joint.shapes.standard.Link();
         
            link.source(cbl0);
            link.target(tl2);
        
        link.connector('rounded', { radius: 20 });
        link.connector('smooth');
        link.addTo(graph);
    
        var link = new joint.shapes.standard.Link();
        
            link.source(tl3);
            link.target(cbl2);
        
        link.connector('rounded', { radius: 20 });
        link.connector('smooth');
        link.addTo(graph);
    


    
        var link = new joint.shapes.standard.Link();
        link.source(cbl0);
        link.target(cbl1);
        link.connector('rounded', { radius: 20 });
        link.connector('smooth');
        link.attr('line/stroke', '#AA2244');
        link.addTo(graph);
    
        var link = new joint.shapes.standard.Link();
        link.source(cbl0);
        link.target(cbl2);
        link.connector('rounded', { radius: 20 });
        link.connector('smooth');
        link.attr('line/stroke', '#AA2244');
        link.addTo(graph);
    
        var link = new joint.shapes.standard.Link();
        link.source(cbl1);
        link.target(cbl0);
        link.connector('rounded', { radius: 20 });
        link.connector('smooth');
        link.attr('line/stroke', '#AA2244');
        link.addTo(graph);
    
        var link = new joint.shapes.standard.Link();
        link.source(cbl1);
        link.target(cbl3);
        link.connector('rounded', { radius: 20 });
        link.connector('smooth');
        link.attr('line/stroke', '#AA2244');
        link.addTo(graph);
    
        var link = new joint.shapes.standard.Link();
        link.source(cbl2);
        link.target(cbl0);
        link.connector('rounded', { radius: 20 });
        link.connector('smooth');
        link.attr('line/stroke', '#AA2244');
        link.addTo(graph);
    
        var link = new joint.shapes.standard.Link();
        link.source(cbl3);
        link.target(cbl1);
        link.connector('rounded', { radius: 20 });
        link.connector('smooth');
        link.attr('line/stroke', '#AA2244');
        link.addTo(graph);
    


//
//        var link = new joint.shapes.standard.Link();
//        link.source(rect);
//        link.target(rect2);
//        link.addTo(graph);