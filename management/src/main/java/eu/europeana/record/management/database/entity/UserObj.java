/*
 * Copyright 2007-2012 The Europeana Foundation
 *
 *  Licenced under the EUPL, Version 1.1 (the "Licence") and subsequent versions as approved
 *  by the European Commission;
 *  You may not use this work except in compliance with the Licence.
 * 
 *  You may obtain a copy of the Licence at:
 *  http://joinup.ec.europa.eu/software/page/eupl
 *
 *  Unless required by applicable law or agreed to in writing, software distributed under
 *  the Licence is distributed on an "AS IS" basis, without warranties or conditions of
 *  any kind, either express or implied.
 *  See the Licence for the specific language governing permissions and limitations under
 *  the Licence.
 */
package eu.europeana.record.management.database.entity;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.EnumType;
import javax.persistence.Enumerated;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.NamedQueries;
import javax.persistence.NamedQuery;
import javax.persistence.Table;

import eu.europeana.record.management.database.dao.DBEntity;
import eu.europeana.record.management.database.enums.Role;

/**
 * A User representation
 * 
 * @author Yorgos.Mamakis@ kb.nl
 * 
 */
@Entity
@Table(name = "USERS")
@NamedQueries({
		@NamedQuery(name = "findUsers", query = "Select u from UserObj u where u.username= ?1 and u.active=true"),
		@NamedQuery(name = "findAllUsers", query = "Select u from UserObj u where u.active=true"),
		@NamedQuery(name = "findInactiveUsers", query = "Select u from UserObj u where u.username= ?1") })
public class UserObj implements DBEntity {

	/**
	 * 
	 */
	private static final long serialVersionUID = 5229410848838413358L;

	private Long id;

	private String username;

	private String password;

	private Role role;

	private String name;

	private String surname;

	private Boolean active;

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	@Column(name = "ID", nullable = false)
	public Long getId() {

		return this.id;
	}

	/**
	 * The username of the user
	 * 
	 * @return
	 */
	@Column(name = "USERNAME", unique = true, updatable = true)
	public String getUsername() {
		return username;
	}

	public void setUsername(String username) {
		this.username = username;
	}

	/**
	 * THe password of the user
	 * 
	 * @return
	 */
	@Column(name = "PASSWORD")
	public String getPassword() {
		return password;
	}

	public void setPassword(String password) {
		this.password = password;
	}

	/**
	 * The role of the user (USER,USERADMIN,GOD)
	 * 
	 * @return
	 */
	@Column(name = "ROLE")
	@Enumerated(EnumType.STRING)
	public Role getRole() {
		return role;
	}

	public void setRole(Role role) {
		this.role = role;
	}

	@Column(name = "NAME")
	public String getName() {
		return name;
	}

	/**
	 * The name of the user
	 * 
	 * @param name
	 */
	public void setName(String name) {
		this.name = name;
	}

	@Column(name = "SURNAME")
	public String getSurname() {
		return surname;
	}

	/**
	 * The surname of the user
	 * 
	 * @param surname
	 */

	public void setSurname(String surname) {
		this.surname = surname;
	}

	public void setId(Long id) {
		this.id = id;
	}

	@Column(name = "ACTIVE")
	public Boolean getActive() {
		return active;
	}

	public void setActive(Boolean active) {
		this.active = active;
	}

	@Override
	public String toString() {
		return "User: [username: " + this.username + ", name: " + this.name + ", surname: " + this.surname + ", Role: "
				+ this.role + "]";

	}

}
