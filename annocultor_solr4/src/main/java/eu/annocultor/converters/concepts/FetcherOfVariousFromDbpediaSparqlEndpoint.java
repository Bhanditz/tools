/*
 * Copyright 2005-2009 the original author or authors.
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *      http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package eu.annocultor.converters.concepts;

import java.io.File;
import java.net.URL;
import java.util.HashMap;
import java.util.Map;

import eu.annocultor.context.Environment;
import eu.annocultor.context.EnvironmentImpl;
import eu.annocultor.tagger.vocabularies.Vocabulary.NormaliseCaller;
import eu.annocultor.tagger.vocabularies.VocabularyOfTerms;


/**
 * Tagging (aka semantic enrichment) of records from SOLR.
 * 
 * @author Borys Omelayenko
 *
 */
public class FetcherOfVariousFromDbpediaSparqlEndpoint 
{
    protected VocabularyOfTerms vocabularyOfConcepts = new VocabularyOfTerms("dbpedia.selected.concepts", null) {

        @Override
        public String onNormaliseLabel(String label, NormaliseCaller caller) throws Exception {
            return label;
        }

    };

    protected Environment environment = new EnvironmentImpl();
 
    public void fetch() throws Exception {

         String[] dbpediaResources = {
                "Art",
                "Architecture",
                "Art_Deco",
                "Art_Nouveau",
                "Baroque",
                "Cubism",
                "Contemporary_art",
                "Dada",
                "Digital_art",
                "Expressionism",
                "Fine-art_photography",
                "Folk_art",
                "Futurism",
                "Impressionism",
                "Neoclassicism",
                "Pre-Raphaelite_Brotherhood",
                "Kitsch",
                "Still_life",
                "Landscape",
                "Minimalism",
                "Modernism",
                "Renaissance",
                "Realism_(arts)",
                "Romanesque_art",
                "Romanticism",
                "Rococo",
                "Pastoral",
                "Portrait",
                "Street_art",
                "Surrealism",
                "Symbolism",
                "Music",
                "Theatre",
                "Painting",
                "Sculpture",
                "Drawing",
                "Poster",
                "Photograph",
                "Furniture",
                "Costume",
                "Fashion",
                "Jewellery",
                "Porcelain",
                "Tapestry",
                "Woodcut"
        };

        File cacheDir = new File(environment.getVocabularyDir() + "/tmp");

        for (String resource : dbpediaResources) {
            try {
            String query = makeDbpediaSparqlQuery(resource, "label", "rdfs:label");
            vocabularyOfConcepts.loadTermsFromSparqlEndpoint(query, cacheDir, new URL("http://dbpedia.org/sparql"));    
            } catch (Exception e) {
                System.out.println("dbpedia resource " + resource + " does not have anything under it");
            }
        }
    }

    String makeDbpediaSparqlQuery(String resource, String field, String property) {
        return
        "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " +
        "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> " +
        "PREFIX foaf: <http://xmlns.com/foaf/0.1/> " +
        "PREFIX dbo: <http://dbpedia.org/ontology/> " +
        "SELECT <http://dbpedia.org/resource/" + resource + "> ?" + field + " WHERE { " +
        " <http://dbpedia.org/resource/" + resource + "> " + property + " ?" + field + " " + 
        " } " ;
    }

    public void save() throws Exception {
        environment.getNamespaces().addNamespace("http://dbpedia.org/ontology/", "dbpedia");
        Map<String, String> propertiesToExport = new HashMap<String, String>();
//        propertiesToExport.put("birth", "dbpedia:birth");
//        propertiesToExport.put("death", "dbpedia:death");
        
        vocabularyOfConcepts.saveAsRDF(
                "Selection from DBPedia: various concepts \n" 
                + "Extracted from http://dbpedia.org/snorql/ \n"
                + "Original data is distributed under the GNU General Public License", 
                environment.getNamespaces(),
                propertiesToExport, 
                null);
    }
    
    public static void main(String[] args) throws Exception {
        FetcherOfVariousFromDbpediaSparqlEndpoint fetcher = new FetcherOfVariousFromDbpediaSparqlEndpoint();
        fetcher.fetch();
        fetcher.save();
    }

 }
