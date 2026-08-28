\name{application-contract}
\alias{read_training_request}
\alias{write_training_request}
\alias{process_training_request}
\title{Application request and result contract}
\description{
  Read, write, and process the versioned transport-neutral application
  request envelope.  Processing dispatches explicitly to the existing native
  engine operations and returns normal domain outcomes as a result list.
}
\usage{
read_training_request(path)
write_training_request(request, path = NULL, pretty = TRUE)
process_training_request(request, db, relationships = NULL)
}
\arguments{
  \item{path}{Path to a JSON request document.}
  \item{request}{A canonical request list or request JSON path.}
  \item{db}{A loaded DB++ database document, normally from \code{load_database()}.}
  \item{relationships}{An optional loaded relationship document.}
  \item{pretty}{Whether to pretty-print JSON when writing.}
}
\value{A canonical request or result list; \code{write_training_request} invisibly returns the JSON string or writes it to \code{path}.}
\seealso{\code{load_database}, \code{resolve_intent}, \code{generate_plan}}
