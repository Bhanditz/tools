/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package eu.europeana.record.management.server;

import eu.europeana.record.management.server.components.SolrServer;
import eu.europeana.record.management.shared.dto.Record;

/**
 *
 * @author ymamakis
 */
public class MongoServerTest {
    public static void main(String[] args){
        SolrServer server = new  SolrServer();
        server.setUrl("http://sandbox41.isti.cnr.it:9191/solr/search");
        Record record= new Record();
        record.setField("europeana_id");
        record.setValue("/9200326/BibliographicResource_30000591311771");
        System.out.println(""+(null==server.identifyRecord(record)));
                
    }
}
