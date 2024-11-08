import (
    "github.com/go-playground/validator/v10"
)

type UserDTO struct {
    ID       int    `json:"id"`
    Name     string `json:"name" validate:"required"`
    Email    string `json:"email" validate:"email"`
    Password string `json:"password,omitempty" validate:"min=8"`
}

type PreSavePincodeCmd struct {
	PinCode  string
	PersonID string
}

type PreSavePincodeResult struct {
	PreSavePinCodeID string
}

type UpdateCodewordCmd struct {
	PersonID          string
	EncryptedCodeword string
}

type CreateFullAccessRecoveryAuthorizedCmd struct {
	ClientID           string
	PeriodAfterExpires time.Duration
}

type FullAccessRecoveryComment struct {
	ID        string                  `db:"id"`
	CreatedAt time.Time               `db:"created_at"`
	SupportID string                  `db:"support_id"`
	IssueID   string                  `db:"issue_id"`
}