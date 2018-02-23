package eu.europeana.organization.model;

import java.util.List;

/**
 * This API defines methods for Zoho organization object.
 * @author GrafR
 *
 */
public interface ZohoOrganization {
	
	String getZohoId();
	String getOrganizationName();
	List<String> getAlternativeOrganizationName();
	String getOrganizationOwner();
	String getAcronym();
	String getDomain();
	String getOrganizationCountry();
	String getSector();
	String getLogo();
	String getWebsite();
	String getLanguage();
	List<String> getAlternativeLanguage();
	String getRole();
	String getScope();
	String getGeographicLevel();
	String getModifiedBy();
	List<String> getSameAs();
	String getPostBox();
	String getHasAddress();
	String getStreet();
	String getCity();
	String getZipCode();
	String getCountry();
	String getDescription();

}
