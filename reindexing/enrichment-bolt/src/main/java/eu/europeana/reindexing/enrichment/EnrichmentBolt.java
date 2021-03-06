/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package eu.europeana.reindexing.enrichment;

import backtype.storm.task.OutputCollector;
import backtype.storm.task.TopologyContext;
import backtype.storm.topology.OutputFieldsDeclarer;
import backtype.storm.topology.base.BaseRichBolt;
import backtype.storm.tuple.Fields;
import backtype.storm.tuple.Tuple;
import com.mongodb.Mongo;
import com.mongodb.ServerAddress;
import eu.europeana.corelib.edm.exceptions.MongoDBException;
import eu.europeana.corelib.mongo.server.impl.EdmMongoServerImpl;
import eu.europeana.corelib.solr.bean.impl.FullBeanImpl;
import eu.europeana.corelib.solr.entity.ProxyImpl;
import eu.europeana.enrichment.api.external.EntityWrapper;
import eu.europeana.enrichment.api.external.EntityWrapperList;
import eu.europeana.enrichment.api.external.InputValue;
import eu.europeana.enrichment.rest.client.EnrichmentDriver;
import eu.europeana.reindexing.common.ReindexingFields;
import eu.europeana.reindexing.common.ReindexingTuple;
import org.apache.commons.codec.binary.Base64;
import org.codehaus.jackson.map.ObjectMapper;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.UnknownHostException;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.zip.GZIPOutputStream;

/**
 *
 * @author ymamakis
 */
public class EnrichmentBolt extends BaseRichBolt {
    private OutputCollector collector;
    
    private ObjectMapper om;
    private EnrichmentDriver driver;
    private EdmMongoServerImpl mongoServer;
    private String path;
    private String[] mongoAddresses;
    String dbName;
    String dbUser;
    String dbPassword;
    
    public EnrichmentBolt(String path, String[] mongoAddresses, String dbName, String dbUser, String dbPassword) {
        this.path = path;
        this.mongoAddresses = mongoAddresses;
        this.dbName = dbName;
        this.dbUser = dbUser;
        this.dbPassword = dbPassword;
    }

    
    
    
    @Override
    public void declareOutputFields(OutputFieldsDeclarer ofd) {
        ofd.declare(new Fields(ReindexingFields.TASKID, ReindexingFields.BATCHID,ReindexingFields.IDENTIFIER, ReindexingFields.NUMFOUND, ReindexingFields.QUERY, ReindexingFields.ENTITYWRAPPER,ReindexingFields.EDMXML));
    }

    @Override
    public void prepare(Map map, TopologyContext tc, OutputCollector oc) {
        try {
            this.collector = oc;
            driver = new EnrichmentDriver(path);
            om = new ObjectMapper();
            List<ServerAddress> addresses = new ArrayList<>();
            for (String mongoStr : mongoAddresses) {
                try {
                    ServerAddress address;
                    
                    address = new ServerAddress(mongoStr, 27017);
                    addresses.add(address);
                    
                    
                } catch (UnknownHostException ex) {
                    Logger.getLogger(EnrichmentBolt.class.getName()).log(Level.SEVERE, null, ex);
                    
                }
            }
          //  List<MongoCredential> credentialsList = new ArrayList<MongoCredential>();
          //  MongoCredential credential = MongoCredential.createCredential(dbUser, dbName, dbPassword.toCharArray());
           // credentialsList.add(credential);
          //  MongoClient mongo = new MongoClient(addresses, credentialsList);
            Mongo mongo = new Mongo(addresses);
            mongoServer = new EdmMongoServerImpl(mongo, dbName, null, null);
        } catch (MongoDBException ex) {
            Logger.getLogger(EnrichmentBolt.class.getName()).log(Level.SEVERE, null, ex);
        }
    }

    @Override
    public void execute(Tuple tuple) {
        ReindexingTuple task = ReindexingTuple.fromTuple(tuple);
        try {
			FullBeanImpl fBean = mongoServer.searchByAbout(FullBeanImpl.class, task.getIdentifier());

			// cleanFullBean(fBean);
			List<InputValue> values = getEnrichmentFields(fBean);
			List<EntityWrapper> entities = new ArrayList<>();
			long startEnrich = new Date().getTime();
			if (values.size() > 0) {
				entities = driver.enrich(values, false);
			}
			//Logger.getGlobal().log(Level.INFO, "*** Enrichment for " + fBean.getAbout() + " took " + (new Date().getTime() - startEnrich) + " ms ***");
			EntityWrapperList lst = new EntityWrapperList();
			lst.setWrapperList(entities);
			// appendEntities(fBean, entities);
			long startConvert = new Date().getTime();
			// String enrichments = om.writeValueAsString(lst);

			ByteArrayOutputStream byteOutput = new ByteArrayOutputStream(1024);
			om.writeValue(new GZIPOutputStream(byteOutput), lst);
			String enrichments = new Base64().encodeAsString(byteOutput
					.toByteArray());

			//Logger.getGlobal().log( Level.INFO, "*** Converting to String for enriched " + fBean.getAbout()
			//				+ " took " + (new Date().getTime() - startConvert) + " ms ***");
			collector.emit(new ReindexingTuple(task.getTaskId(), task.getBatchId(), task .getIdentifier(), task.getNumFound(), task.getQuery(), enrichments,null).toTuple());
        } catch (IOException ex) {
            Logger.getLogger(EnrichmentBolt.class.getName()).log(Level.SEVERE, null, ex);
        }

    }

    private List<InputValue> getEnrichmentFields(FullBeanImpl fBean) {
        ProxyImpl providerProxy = null;
        if(fBean!=null&& fBean.getProxies()!=null) {
            for (ProxyImpl proxy : fBean.getProxies()) {
                if (!proxy.isEuropeanaProxy()) {
                    providerProxy = proxy;
                    break;
                }
            }
            return EnrichmentFieldsCreator.extractEnrichmentFieldsFromProxy(providerProxy);
        }
        return new ArrayList<>();
    }

   
}
