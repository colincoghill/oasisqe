

At the moment this is a collection of notes, that I will slowly extend and may one day grow up to
be a manual. Borrow liberally from the 2004 user manual.



# Installation

see REQUIREMENTS.md and INSTALL.md

## What are the core configuration options?


# Setup

# Users

Describe common configurations, eg. with server auth, or with spreadsheet enrolment feeds.

# Permissions

## How do the course permissions work.
## How to assign them.


# Courses

## What is a course, how are OASIS topics arranged.

A course is, essentially, a collection of people, questions, and assessments. The usual structure is to arrange these
by topic to mirror an existing school/university course, but it could be done other ways.

Every course has a single course administrator, who is primarily responsible for the overall running of the course in OASIS.
They can do everything themselves, or they can assign permissions to others. Permissions are fairly granular, for
example it's possible to assign an assistant to create and check questions in the course - they will not automatically
gain access to students' assessment marks, or be able to see assessments in advance.




## Adding a Course:

Log in as administrator, and navigate to Setup -> Server Administration -> Courses


You should see a listing of courses in the system (if any), and a button allowing you to "Add Course". Press this.

[SCREENSHOT]

Choose a name and a title for the course. The name should be something short. For universities an appropriate name
might be the course code, eg. "PHYSICS101".  The title is a longer name, eg. "Introduction to Physics".


Next, decide who controls how students will be associated with the course:

[SCREENSHOT]

### "Open"

   This means any student with a valid OASIS account can sign themselves up for the course and do assessments. This
   is appropriate for optional content or self-training setups.

### "Course Admin"

   The course administrator controls the course. They can choose if it's open, or can add users themselves, including
   by linking to spreadsheets or web services.

### "Central"

   The course administrator cannot change the course membership, usually because it is provided externally.


If you choose "Central", a few more options will appear letting you set up a feed of enrolment information.


  *   "HTTP List"
              Will ask for the URL (and optional authentication information) where OASIS can retrieve class lists.

  *   "Server List"
              Will ask for a filename to load the class lists from. This should be placed on the server in the folder configured as "enrol_file_path" in the oasisqe.ini config file.

  *   "Manual"
              The Administrator can upload lists or add users manually. This is not recommended as it's quite time consuming.


## Enrolment List Format

   The enrolment lists tell OASIS who is a member of a course. They are very simple, just a single column list of usernames:

```
vdinkley
fjones
dblake
nrogers
sdoo
```

   This can be created in Excel, or in a simple text editor. If you are fetching the data from a central system, eg. from a database
   query, it should be possible to produce this automatically. [ PHP example ? ]


# Scheduler


* What gets run, when. What does it do. Implications.


# Examples



1. Local courses, open enrolment only.



2. Set up with server auth, enrolment via spreadsheet.



# Questions

## What's possible?

## Features.

## The parts of a question. Basic tutorial.


# Assessments

## What's possible

## Setting up an Assessment

## Examples



## Advice



# Admin

## Setup and troubleshooting
## Monitoring
## Performance
## Scaling


# Teaching

Advice and recommendations.

## Question design
## Use in a course
## Assessments


# Development

## Advanced questions

### Anatomy of an OASIS "raw" question


## Improving OASIS itself.

### System layout
### Coding Guidelines
### Data migration
### Testing
