"""MCP tool definitions for CRM MCP Server."""


def get_all_tools():
    """Get all tool definitions for CRM MCP Server.

    Returns:
        List of tool definition dictionaries
    """
    return [
        # Search & Read Tools (4)
        {
            "name": "search_account",
            "description": "Search for companies (accounts) in the CRM. Supports fuzzy search with multiple retry strategies.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Organization/company name to search for (partial matches supported)"
                    },
                    "ort": {
                        "type": "string",
                        "description": "City (Ort) filter for billing address"
                    }
                },
                "required": []
            }
        },
        {
            "name": "search_person",
            "description": "Search for people (contacts) in the CRM. Supports fuzzy search on last name.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "vorname": {
                        "type": "string",
                        "description": "First name (Vorname)"
                    },
                    "nachname": {
                        "type": "string",
                        "description": "Last name (Nachname)"
                    },
                    "firma": {
                        "type": "string",
                        "description": "Company/organization name filter"
                    }
                },
                "required": []
            }
        },
        {
            "name": "search_potential",
            "description": "Search for sales potentials in the CRM. Supports status filtering and fuzzy search.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Potential name to search for"
                    },
                    "firma": {
                        "type": "string",
                        "description": "Company/organization name filter"
                    },
                    "inhaber": {
                        "type": "string",
                        "description": "Owner (zuständig) filter"
                    },
                    "status": {
                        "type": "string",
                        "description": "Status filter",
                        "enum": ["inaktiv", "gewonnen", "verloren", "gestorben", ""]
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_comments",
            "description": "Extract comments from an account's detail view.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Account record ID"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of comments to retrieve (default: 5)",
                        "default": 5
                    }
                },
                "required": ["account_id"]
            }
        },

        # Create Tools with Duplicate Checking (3)
        {
            "name": "create_account",
            "description": "Create a new company (account) after checking for duplicates. Returns error if similar accounts exist.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "object",
                        "description": "Account data including accountname (required), bill_city, website, phone, etc.",
                        "properties": {
                            "accountname": {
                                "type": "string",
                                "description": "Company/organization name (required)"
                            },
                            "bill_city": {
                                "type": "string",
                                "description": "Billing city"
                            },
                            "bill_street": {
                                "type": "string",
                                "description": "Billing street address"
                            },
                            "bill_code": {
                                "type": "string",
                                "description": "Billing postal code"
                            },
                            "phone": {
                                "type": "string",
                                "description": "Phone number"
                            },
                            "website": {
                                "type": "string",
                                "description": "Website URL"
                            }
                        },
                        "required": ["accountname"]
                    }
                },
                "required": ["data"]
            }
        },
        {
            "name": "create_person",
            "description": "Create a new contact (person) linked to a company after checking for duplicates.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "firma_id": {
                        "type": "string",
                        "description": "Account (company) record ID to link the contact to"
                    },
                    "data": {
                        "type": "object",
                        "description": "Contact data including firstname, lastname, email, phone, etc.",
                        "properties": {
                            "firstname": {
                                "type": "string",
                                "description": "First name"
                            },
                            "lastname": {
                                "type": "string",
                                "description": "Last name"
                            },
                            "email": {
                                "type": "string",
                                "description": "Email address"
                            },
                            "phone": {
                                "type": "string",
                                "description": "Phone number"
                            },
                            "mobile": {
                                "type": "string",
                                "description": "Mobile phone number"
                            },
                            "title": {
                                "type": "string",
                                "description": "Job title"
                            }
                        },
                        "required": []
                    }
                },
                "required": ["firma_id", "data"]
            }
        },
        {
            "name": "create_potential",
            "description": "Create a new sales potential linked to a company.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "firma_id": {
                        "type": "string",
                        "description": "Account (company) record ID to link the potential to"
                    },
                    "data": {
                        "type": "object",
                        "description": "Potential data including potentialname (required), amount, closingdate, etc.",
                        "properties": {
                            "potentialname": {
                                "type": "string",
                                "description": "Potential name (required)"
                            },
                            "amount": {
                                "type": "string",
                                "description": "Potential amount/value"
                            },
                            "closingdate": {
                                "type": "string",
                                "description": "Expected closing date (YYYY-MM-DD)"
                            },
                            "sales_stage": {
                                "type": "string",
                                "description": "Sales stage/status"
                            },
                            "probability": {
                                "type": "string",
                                "description": "Probability of closing (%)"
                            }
                        },
                        "required": ["potentialname"]
                    }
                },
                "required": ["firma_id", "data"]
            }
        },

        # Update Tools (3)
        {
            "name": "update_account",
            "description": "Update fields on an existing account (company).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Account record ID to update"
                    },
                    "updates": {
                        "type": "object",
                        "description": "Dictionary of field names and new values to update",
                        "additionalProperties": True
                    }
                },
                "required": ["account_id", "updates"]
            }
        },
        {
            "name": "update_person",
            "description": "Update fields on an existing contact (person).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "person_id": {
                        "type": "string",
                        "description": "Contact record ID to update"
                    },
                    "updates": {
                        "type": "object",
                        "description": "Dictionary of field names and new values to update",
                        "additionalProperties": True
                    }
                },
                "required": ["person_id", "updates"]
            }
        },
        {
            "name": "update_potential",
            "description": "Update fields on an existing sales potential.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "potential_id": {
                        "type": "string",
                        "description": "Potential record ID to update"
                    },
                    "updates": {
                        "type": "object",
                        "description": "Dictionary of field names and new values to update",
                        "additionalProperties": True
                    }
                },
                "required": ["potential_id", "updates"]
            }
        },

        # Interaction Tool (1)
        {
            "name": "add_comment_to_account",
            "description": "Add a comment to an account's detail view.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Account record ID"
                    },
                    "autor": {
                        "type": "string",
                        "description": "Comment author name"
                    },
                    "text": {
                        "type": "string",
                        "description": "Comment text content"
                    }
                },
                "required": ["account_id", "autor", "text"]
            }
        }
    ]
